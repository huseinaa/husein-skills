"""Mutation testing on changed lines only. No dependencies, works on Windows.

Plants one small bug at a time in the changed lines, runs the tests, and puts the file back.
A mutant the tests catch is "killed". One they miss "survived": that is a missing test.

Usage:
    python mutate.py --cwd PROJECT_DIR --cmd "TEST COMMAND" FILE:RANGES [FILE:RANGES ...]
        FILE is relative to --cwd, RANGES like 10-40,55,60-62
    options:
        --max N          cap on mutants (default from config.json), sampled evenly
        --timeout S      per-mutant timeout cap (default from config.json)
        --json PATH      also write the full result as JSON
        --list           only list the mutants, run nothing
        --recover        only restore files left mutated by a crashed run

Every file is restored after every mutant (original kept in memory and in a backup under the
temp folder). Any run first restores files a crashed earlier run left mutated.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, asdict
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
CONFIG = json.loads((SKILL_DIR / "config.json").read_text(encoding="utf-8"))
BACKUP_DIR = Path(tempfile.gettempdir()) / "feature-testing-backups"
PYCACHE_DIR = Path(tempfile.gettempdir()) / "feature-testing-pycache"

PY_EXT = {".py"}
JS_EXT = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
JSX_EXT = {".jsx", ".tsx"}

CMP = r"(?:<=|>=|==|!=|===|!==|(?<![<>=!-])<(?![<=])|(?<![-=])>(?![>=]))"
SP = r"(?<=\s){op}(?=\s)"


@dataclass
class Mutant:
    file: str
    line: int
    kind: str
    original: str
    mutated: str
    status: str = "pending"   # killed | survived | timeout | invalid
    seconds: float = 0.0


# ---------------------------------------------------------------- recovery

def backup_path(path: Path) -> Path:
    return BACKUP_DIR / (hashlib.sha1(str(path.resolve()).encode()).hexdigest() + ".json")


def write_backup(path: Path, data: bytes) -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_path(path).write_text(json.dumps({
        "path": str(path.resolve()),
        "data": base64.b64encode(data).decode(),
    }), encoding="utf-8")


def drop_backup(path: Path) -> None:
    try:
        backup_path(path).unlink()
    except FileNotFoundError:
        pass


def recover() -> list[str]:
    restored = []
    if not BACKUP_DIR.exists():
        return restored
    for b in BACKUP_DIR.glob("*.json"):
        try:
            info = json.loads(b.read_text(encoding="utf-8"))
            target = Path(info["path"])
            data = base64.b64decode(info["data"])
            if not target.exists() or target.read_bytes() != data:
                target.write_bytes(data)
                restored.append(str(target))
            b.unlink()
        except Exception as exc:  # keep the backup if we could not use it
            print(f"warning: could not use backup {b}: {exc}", file=sys.stderr)
    return restored


# ---------------------------------------------------------------- code mask

def code_mask(text: str, lang: str) -> list[bool]:
    """True for characters that are code, False inside strings and comments."""
    mask = [True] * len(text)
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if lang == "py" and c == "#":
            while i < n and text[i] != "\n":
                mask[i] = False
                i += 1
            continue
        if lang == "js" and text.startswith("//", i):
            while i < n and text[i] != "\n":
                mask[i] = False
                i += 1
            continue
        if lang == "js" and text.startswith("/*", i):
            end = text.find("*/", i + 2)
            end = n if end < 0 else end + 2
            for k in range(i, end):
                mask[k] = False
            i = end
            continue
        quotes = "'\"" if lang == "py" else "'\"`"
        if c in quotes:
            triple = lang == "py" and text.startswith(c * 3, i)
            q = c * 3 if triple else c
            j = i + len(q)
            while j < n:
                if text[j] == "\\":
                    j += 2
                    continue
                if text.startswith(q, j):
                    j += len(q)
                    break
                if text[j] == "\n" and not triple and c != "`":
                    break
                j += 1
            for k in range(i, min(j, n)):
                mask[k] = False
            i = j
            continue
        i += 1
    return mask


# ---------------------------------------------------------------- operators

def ops_for(lang: str, jsx: bool) -> list[tuple[str, str, str]]:
    """(kind, regex, replacement) applied inside one line, code characters only."""
    common = [
        ("< to <=", SP.format(op="<"), "<="),
        ("> to >=", SP.format(op=">"), ">="),
        ("<= to <", SP.format(op="<="), "<"),
        (">= to >", SP.format(op=">="), ">"),
        ("+ to -", SP.format(op=r"\+"), "-"),
        ("- to +", SP.format(op="-"), "+"),
        ("* to /", SP.format(op=r"\*"), "/"),
    ]
    if jsx:
        common = [o for o in common if o[0][0] not in "<>"]
    if lang == "py":
        return [
            ("== to !=", SP.format(op="=="), "!="),
            ("!= to ==", SP.format(op="!="), "=="),
            *common,
            ("and to or", r"\band\b", "or"),
            ("or to and", r"\bor\b", "and"),
            ("drop not", r"\bnot\s+", ""),
            ("True to False", r"\bTrue\b", "False"),
            ("False to True", r"\bFalse\b", "True"),
        ]
    return [
        ("=== to !==", SP.format(op="==="), "!=="),
        ("!== to ===", SP.format(op="!=="), "==="),
        ("== to !=", SP.format(op="=="), "!="),
        ("!= to ==", SP.format(op="!="), "=="),
        *common,
        ("&& to ||", SP.format(op="&&"), "||"),
        ("|| to &&", SP.format(op=r"\|\|"), "&&"),
        ("true to false", r"\btrue\b", "false"),
        ("false to true", r"\bfalse\b", "true"),
        ("drop !", r"(?<![!=\w)\]])!(?=[\w(])", ""),
    ]


PY_NO_DELETE = re.compile(
    r"^(return|def|class|import|from|if|elif|else|for|while|try|except|finally|with|async|await\s+def|pass|"
    r"yield|global|nonlocal|@|\)|\]|\}|case|match)\b"
)
JS_NO_DELETE = re.compile(
    r"^(return|const|let|var|function|class|import|export|if|else|for|while|do|switch|case|default|try|"
    r"catch|finally|type|interface|enum|declare|\}|\)|\]|<|async\s+function)\b"
)


def balanced(s: str) -> bool:
    return all(s.count(a) == s.count(b) for a, b in ("()", "[]", "{}"))


def line_mutants(line: str, mask: list[bool], lang: str, jsx: bool) -> list[tuple[str, str]]:
    body = line.rstrip("\r\n")
    stripped = body.strip()
    if not stripped or not any(mask[: len(body)]):
        return []
    first = next((i for i, ch in enumerate(body) if not ch.isspace()), 0)
    if not mask[first]:
        return []  # line starts inside a string or comment (docstring, comment line)
    if lang == "py" and re.match(r"^(import|from)\b", stripped):
        return []
    if lang == "js" and re.match(r"^(import|export\s+\{|export\s+\*|type|interface)\b", stripped):
        return []

    out: list[tuple[str, str]] = []
    seen: set[str] = set()

    def add(kind: str, new: str) -> None:
        if new != body and new not in seen:
            seen.add(new)
            out.append((kind, new))

    for kind, rx, rep in ops_for(lang, jsx):
        for m in re.finditer(rx, body):
            if all(mask[k] for k in range(m.start(), m.end())):
                add(kind, body[: m.start()] + rep + body[m.end():])

    # boundary: integers on lines that compare something
    code_only = "".join(ch if mask[k] else " " for k, ch in enumerate(body))
    if re.search(CMP, code_only) or "range(" in code_only:
        for m in re.finditer(r"(?<![\w.])\d+(?![\w.])", body):
            if all(mask[k] for k in range(m.start(), m.end())):
                add("number +1", body[: m.start()] + str(int(m.group()) + 1) + body[m.end():])

    indent = body[:first]
    if lang == "py":
        m = re.match(r"^(\s*return\s+)(.+?)\s*$", body)
        if m and m.group(2) != "None" and mask[m.start(2)]:
            add("return None", m.group(1) + "None")
        m = re.match(r"^(\s*(?:if|elif|while)\s+)(.+)(:\s*)$", body)
        if m and all(mask[k] for k in range(m.start(2), m.end(2))):
            add("negate condition", f"{m.group(1)}not ({m.group(2)}){m.group(3)}")
        if not PY_NO_DELETE.match(stripped) and not stripped.endswith((":", ",", "\\", "(", "[", "{")):
            add("skip statement", indent + "pass")
    else:
        m = re.match(r"^(\s*return\s+)(.+?);?\s*$", body)
        if m and m.group(2) not in ("null", "undefined") and mask[m.start(2)]:
            add("return null", m.group(1) + "null;")
        if (stripped.endswith(";") and balanced(stripped) and not JS_NO_DELETE.match(stripped)
                and not stripped.startswith(("//", "*"))):
            add("skip statement", indent + ";")
    return out


def parse_ranges(spec: str) -> list[tuple[int, int]]:
    out = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            out.append((int(a), int(b)))
        else:
            out.append((int(part), int(part)))
    return out


def generate(cwd: Path, targets: list[tuple[str, list[tuple[int, int]]]]) -> list[Mutant]:
    mutants: list[Mutant] = []
    for rel, ranges in targets:
        path = cwd / rel
        ext = path.suffix
        if ext not in PY_EXT | JS_EXT:
            continue
        lang = "py" if ext in PY_EXT else "js"
        text = path.read_bytes().decode("utf-8", errors="replace")
        mask = code_mask(text, lang)
        lines = text.splitlines(keepends=True)
        offsets, pos = [], 0
        for ln in lines:
            offsets.append(pos)
            pos += len(ln)
        wanted = {n for a, b in ranges for n in range(a, b + 1)}
        for idx, ln in enumerate(lines, start=1):
            if idx not in wanted:
                continue
            lm = mask[offsets[idx - 1]: offsets[idx - 1] + len(ln)]
            for kind, new in line_mutants(ln, lm, lang, ext in JSX_EXT):
                mutants.append(Mutant(rel, idx, kind, ln.rstrip("\r\n"), new))
    return mutants


def sample(mutants: list[Mutant], cap: int) -> list[Mutant]:
    if len(mutants) <= cap:
        return mutants
    step = len(mutants) / cap
    return [mutants[int(i * step)] for i in range(cap)]


# ---------------------------------------------------------------- running

def apply(text: str, line_no: int, new_body: str) -> str:
    lines = text.splitlines(keepends=True)
    old = lines[line_no - 1]
    ending = old[len(old.rstrip("\r\n")):]
    lines[line_no - 1] = new_body + ending
    return "".join(lines)


def run_cmd(cmd: str, cwd: Path, timeout: float) -> tuple[str, float]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPYCACHEPREFIX"] = str(PYCACHE_DIR)  # never read a stale .pyc of the original
    env.setdefault("CI", "1")
    t0 = time.time()
    p = subprocess.Popen(cmd, cwd=cwd, shell=True, env=env,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        code = p.wait(timeout=timeout)
        return ("passed" if code == 0 else "failed"), time.time() - t0
    except subprocess.TimeoutExpired:
        kill_tree(p)
        return "timeout", time.time() - t0


def kill_tree(p: subprocess.Popen) -> None:
    """Kill the shell and everything under it, so no test keeps running on mutated code."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        p.kill()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        pass


def run(cwd: Path, cmd: str, mutants: list[Mutant], timeout_cap: float) -> float:
    status, base_s = run_cmd(cmd, cwd, timeout_cap)
    if status != "passed":
        print(f"ABORT: the tests do not pass before any mutation ({status}). Make them green first.")
        sys.exit(3)
    timeout = min(timeout_cap, max(10.0, base_s * 3 + 5))
    print(f"baseline green in {base_s:.1f}s, per-mutant timeout {timeout:.0f}s, {len(mutants)} mutants")

    originals: dict[str, bytes] = {}
    try:
        for i, m in enumerate(mutants, 1):
            path = cwd / m.file
            if m.file not in originals:
                originals[m.file] = path.read_bytes()
            raw = originals[m.file]
            text = raw.decode("utf-8", errors="replace")
            new_text = apply(text, m.line, m.mutated)
            if path.suffix in PY_EXT:
                try:
                    compile(new_text, str(path), "exec")
                except SyntaxError:
                    m.status = "invalid"
                    continue
            write_backup(path, raw)
            try:
                path.write_bytes(new_text.encode("utf-8"))
                result, m.seconds = run_cmd(cmd, cwd, timeout)
            finally:
                path.write_bytes(raw)
                drop_backup(path)
            m.status = {"passed": "survived", "failed": "killed", "timeout": "timeout"}[result]
            mark = {"killed": ".", "timeout": "T", "survived": "S"}[m.status]
            print(mark, end="" if i % 50 else "\n", flush=True)
    finally:
        for rel, raw in originals.items():
            p = cwd / rel
            if p.read_bytes() != raw:
                p.write_bytes(raw)
            drop_backup(p)
    print()
    return timeout


def report(mutants: list[Mutant], total_found: int) -> dict:
    valid = [m for m in mutants if m.status in ("killed", "survived", "timeout")]
    killed = sum(m.status in ("killed", "timeout") for m in valid)
    score = round(100 * killed / len(valid), 1) if valid else None
    survivors = [m for m in valid if m.status == "survived"]
    print(f"\nmutants found {total_found}, run {len(valid)}, killed {killed}, "
          f"survived {len(survivors)}, invalid skipped {sum(m.status == 'invalid' for m in mutants)}")
    print(f"mutation score: {score if score is not None else 'n/a'}%  (target {CONFIG['mutation_min']}%)")
    if survivors:
        print("\nSURVIVED (each one is a bug the tests did not notice):")
        for m in survivors:
            print(f"  {m.file}:{m.line}  [{m.kind}]")
            print(f"      was: {m.original.strip()}")
            print(f"      now: {m.mutated.strip()}")
    return {"found": total_found, "run": len(valid), "killed": killed, "survived": len(survivors),
            "score": score, "target": CONFIG["mutation_min"],
            "mutants": [asdict(m) for m in mutants]}


def main(argv: list[str]) -> int:
    cwd, cmd, max_n, timeout_cap, json_out = Path.cwd(), None, CONFIG["max_mutants"], CONFIG["mutant_timeout_s"], None
    list_only = recover_only = False
    targets: list[tuple[str, list[tuple[int, int]]]] = []
    it = iter(argv)
    for a in it:
        if a == "--cwd":
            cwd = Path(next(it)).resolve()
        elif a == "--cmd":
            cmd = next(it)
        elif a == "--max":
            max_n = int(next(it))
        elif a == "--timeout":
            timeout_cap = float(next(it))
        elif a == "--json":
            json_out = Path(next(it))
        elif a == "--list":
            list_only = True
        elif a == "--recover":
            recover_only = True
        else:
            f, _, r = a.rpartition(":")
            if not f or not re.fullmatch(r"[\d,\- ]+", r):
                f, r = a, ""
            targets.append((f, parse_ranges(r) if r else [(1, 10**9)]))

    for p in recover():
        print(f"recovered {p} (left mutated by an earlier run)")
    if recover_only:
        return 0

    found = generate(cwd, targets)
    mutants = sample(found, max_n)
    if list_only:
        for m in mutants:
            print(f"{m.file}:{m.line} [{m.kind}]  {m.mutated.strip()}")
        print(f"{len(mutants)} of {len(found)} mutants")
        return 0
    if not cmd:
        print("--cmd is required")
        return 2
    if not mutants:
        print("no mutants: the changed lines hold nothing to mutate")
        return 0
    run(cwd, cmd, mutants, timeout_cap)
    result = report(mutants, len(found))
    if json_out:
        json_out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
