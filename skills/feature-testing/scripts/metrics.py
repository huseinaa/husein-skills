"""Code quality metrics for the functions touched by a change.

For every function that overlaps a changed line: cyclomatic complexity (how many paths),
length in lines, and deepest nesting of blocks. Flags anything over the limits in config.json.

Usage:
    python metrics.py --cwd PROJECT_DIR FILE:RANGES [FILE:RANGES ...] [--json PATH]

Python is measured exactly with the ast module. JS/TS uses the project's own ESLint when it is
installed (complexity, max-depth, max-lines-per-function), otherwise a brace-matching estimate
marked "estimated".
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mutate import CONFIG, code_mask, parse_ranges  # noqa: E402

LIMITS = {"complexity": CONFIG["complexity_max"], "lines": CONFIG["function_lines_max"],
          "nesting": CONFIG["nesting_max"]}
BLOCKS = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith, ast.Try)
if hasattr(ast, "TryStar"):
    BLOCKS = BLOCKS + (ast.TryStar,)
if hasattr(ast, "Match"):
    BLOCKS = BLOCKS + (ast.Match,)
FUNCS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)
JS_EXT = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
NL = chr(10)


# ---------------------------------------------------------------- python

def own_nodes(fn: ast.AST):
    """Walk a function's body without entering nested functions or classes."""
    stack = list(ast.iter_child_nodes(fn))
    while stack:
        node = stack.pop()
        yield node
        if not isinstance(node, (*FUNCS, ast.ClassDef)):
            stack.extend(ast.iter_child_nodes(node))


def py_complexity(fn: ast.AST) -> int:
    c = 1
    for n in own_nodes(fn):
        if isinstance(n, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.IfExp, ast.ExceptHandler, ast.Assert)):
            c += 1
        elif isinstance(n, ast.BoolOp):
            c += len(n.values) - 1
        elif isinstance(n, ast.comprehension):
            c += 1 + len(n.ifs)
        elif hasattr(ast, "match_case") and isinstance(n, ast.match_case):
            c += 1
    return c


def py_nesting(node: ast.AST, depth: int = 0) -> int:
    best = depth
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (*FUNCS, ast.ClassDef)):
            continue
        d = depth + 1 if isinstance(child, BLOCKS) else depth
        best = max(best, py_nesting(child, d))
    return best


def python_functions(path: Path) -> list[dict]:
    tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    out = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.append({"name": node.name, "start": node.lineno, "end": node.end_lineno,
                        "complexity": py_complexity(node),
                        "lines": node.end_lineno - node.lineno + 1,
                        "nesting": py_nesting(node), "estimated": False})
    return out


# ---------------------------------------------------------------- js / ts: eslint

def find_eslint(cwd: Path) -> Path | None:
    p = cwd
    while True:
        for name in ("eslint.cmd", "eslint"):
            cand = p / "node_modules" / ".bin" / name
            if cand.exists():
                return cand
        if p.parent == p:
            return None
        p = p.parent


def eslint_functions(cwd: Path, files: list[str]) -> dict[str, list[dict]] | None:
    exe = find_eslint(cwd)
    if not exe:
        return None
    cmd = [str(exe), "--format", "json", "--no-warn-ignored",
           "--rule", f"complexity: [warn, {LIMITS['complexity']}]",
           "--rule", f"max-depth: [warn, {LIMITS['nesting']}]",
           "--rule", f"max-lines-per-function: [warn, {{max: {LIMITS['lines']}, skipBlankLines: true, skipComments: true}}]",
           *files]
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=300)
        data = json.loads(p.stdout or "[]")
    except Exception:
        return None
    out: dict[str, list[dict]] = {}
    keep = {"complexity": "complexity", "max-depth": "nesting", "max-lines-per-function": "lines"}
    for f in data:
        rel = Path(f["filePath"]).resolve().relative_to(cwd.resolve()).as_posix()
        for msg in f.get("messages", []):
            metric = keep.get(msg.get("ruleId"))
            if not metric:
                continue
            text = msg.get("message", "")
            nums = re.findall(r"\d+", text)
            name = re.search(r"'([^']+)'", text)
            out.setdefault(rel, []).append({
                "name": name.group(1) if name else "function",
                "start": msg.get("line", 0), "end": msg.get("endLine", msg.get("line", 0)),
                "metric": metric, "value": int(nums[0]) if nums else None,
            })
    return out


# ---------------------------------------------------------------- js / ts: estimate

FN_START = re.compile(
    r"(?:\bfunction\b\s*\*?\s*(\w*)\s*\(|(\w+)\s*[:=]\s*(?:async\s*)?(?:\([^)]*\)|\w+)\s*(?::\s*[^=]+)?=>\s*\{|"
    r"^\s*(?:async\s+)?(?:static\s+)?(?:get\s+|set\s+)?(\w+)\s*\([^)]*\)\s*(?::\s*[^{]+)?\{)"
)
DECISIONS = re.compile(r"\b(if|for|while|case|catch)\b|&&|\|\||\?\?|\?(?![.:?])")
CONTROL = re.compile(r"\b(if|for|while|switch|try|do|else|catch|finally)\b")
NOT_FUNCS = {"if", "for", "while", "switch", "catch", "return"}


def js_estimate(path: Path) -> list[dict]:
    """Brace-matching estimate. Decisions inside nested callbacks count toward the outer function."""
    text = path.read_text(encoding="utf-8", errors="replace")
    mask = code_mask(text, "js")
    code = "".join(ch if mask[i] or ch == NL else " " for i, ch in enumerate(text))
    line_of = [0] * (len(code) + 1)
    n = 1
    for i, ch in enumerate(code):
        line_of[i] = n
        if ch == NL:
            n += 1
    out, pos = [], 0
    for ln in code.splitlines(keepends=True):
        m = FN_START.search(ln)
        if m:
            brace = ln.find("{", m.start())
            name = next((g for g in m.groups() if g), "anonymous")
            if brace >= 0 and name not in NOT_FUNCS:
                out.append(_measure(code, line_of, pos + brace, name))
        pos += len(ln)
    return out


def _measure(code: str, line_of: list[int], open_at: int, name: str) -> dict:
    depth, stack, max_nest, last_break = 0, [], 0, open_at
    end = len(code) - 1
    for i in range(open_at, len(code)):
        ch = code[i]
        if ch == "{":
            depth += 1
            if i != open_at:
                stack.append(bool(CONTROL.search(code[last_break:i])))
                max_nest = max(max_nest, sum(stack))
            last_break = i + 1
        elif ch == "}":
            depth -= 1
            if stack:
                stack.pop()
            last_break = i + 1
            if depth == 0:
                end = i
                break
        elif ch == ";":
            last_break = i + 1
    body = code[open_at:end + 1]
    start_line, end_line = line_of[open_at], line_of[end]
    return {"name": name, "start": start_line, "end": end_line,
            "complexity": 1 + len(DECISIONS.findall(body)),
            "lines": end_line - start_line + 1, "nesting": max_nest, "estimated": True}


# ---------------------------------------------------------------- main

def overlaps(fn: dict, ranges: list[tuple[int, int]]) -> bool:
    return any(a <= fn["end"] and b >= fn["start"] for a, b in ranges)


def parse_args(argv: list[str]):
    cwd, json_out, targets = Path.cwd(), None, []
    it = iter(argv)
    for a in it:
        if a == "--cwd":
            cwd = Path(next(it)).resolve()
        elif a == "--json":
            json_out = Path(next(it))
        else:
            f, _, r = a.rpartition(":")
            if not f or not re.fullmatch(r"[\d,\- ]+", r):
                f, r = a, ""
            targets.append((f, parse_ranges(r) if r else [(1, 10**9)]))
    return cwd, json_out, targets


def collect(cwd: Path, targets) -> tuple[list[dict], bool]:
    rows: list[dict] = []
    js_files = [f for f, _ in targets if Path(f).suffix in JS_EXT]
    eslint = eslint_functions(cwd, js_files) if js_files else None
    for rel, ranges in targets:
        path = cwd / rel
        if not path.exists():
            continue
        if path.suffix == ".py":
            try:
                fns = python_functions(path)
            except SyntaxError as exc:
                rows.append({"file": rel, "name": f"SYNTAX ERROR line {exc.lineno}", "over": ["syntax"]})
                continue
        elif path.suffix in JS_EXT:
            if eslint is not None:
                for v in eslint.get(rel, []):
                    if overlaps(v, ranges):
                        rows.append({"file": rel, "name": v["name"], "start": v["start"],
                                     v["metric"]: v["value"], "over": [v["metric"]]})
                continue
            fns = js_estimate(path)
        else:
            continue
        for fn in fns:
            if overlaps(fn, ranges):
                over = [k for k in LIMITS if fn.get(k) is not None and fn[k] > LIMITS[k]]
                rows.append({"file": rel, **fn, "over": over})
    return rows, eslint is not None


def main(argv: list[str]) -> int:
    cwd, json_out, targets = parse_args(argv)
    rows, used_eslint = collect(cwd, targets)
    print(f"limits: complexity <= {LIMITS['complexity']}, lines <= {LIMITS['lines']}, nesting <= {LIMITS['nesting']}")
    if used_eslint:
        print("JS/TS measured with the project's ESLint (only functions over a limit are listed)")
    for r in rows:
        flag = "OVER " + ",".join(r["over"]) if r.get("over") else "ok"
        est = " (estimated)" if r.get("estimated") else ""
        vals = " ".join(f"{k}={r[k]}" for k in ("complexity", "lines", "nesting") if r.get(k) is not None)
        print(f"  {r['file']}:{r.get('start', '?')} {r['name']}  {vals}  {flag}{est}")
    over = [r for r in rows if r.get("over")]
    print(f"{NL}{len(rows)} functions checked, {len(over)} over a limit")
    if json_out:
        json_out.write_text(json.dumps({"limits": LIMITS, "functions": rows}, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
