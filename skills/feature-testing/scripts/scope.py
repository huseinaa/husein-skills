"""Find what changed and what kind of project it lives in.

Usage:
    python scope.py [repo_dir] [--base REF]

Prints JSON:
{
  "root": "...", "base": "main" | null,
  "projects": [
    {"dir": "...", "stack": "python"|"node", "django": bool,
     "python": "path to interpreter", "test_cmd": "...", "runner": "pytest"|"django"|"vitest"|"jest"|...,
     "code": {"rel/path.py": [[start, end], ...]},     # changed lines, source files
     "tests": {"rel/path_test.py": [[start, end], ...]},
     "logic_lines": 42}
  ],
  "other": ["docs/x.md", ...],       # changed files that are not code (docs, config, styles)
  "logic_lines": 42,                 # changed source lines across all projects, tests excluded
  "small": false                      # true when under config small_change_lines
}

The base is: --base if given; else the merge-base with main/master when on another branch;
else HEAD (so only uncommitted + untracked work counts).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
CONFIG = json.loads((SKILL_DIR / "config.json").read_text(encoding="utf-8"))

PY_EXT = {".py"}
JS_EXT = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
CODE_EXT = PY_EXT | JS_EXT
PY_MARKERS = ("pyproject.toml", "requirements.txt", "setup.py", "setup.cfg", "manage.py")
TEST_RE = re.compile(
    r"(^|/)(tests?|__tests__|spec)(/|$)|(^|/)test_[^/]+\.py$|_test\.py$|\.(test|spec)\.[jt]sx?$|(^|/)conftest\.py$"
)
NON_LOGIC_RE = re.compile(r"(^|/)(migrations)/|\.d\.ts$|(^|/)(next|vite|vitest|jest|eslint|postcss|tailwind)\.config\.")


def git(args: list[str], cwd: Path) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout


def find_root(start: Path) -> Path:
    out = git(["rev-parse", "--show-toplevel"], start).strip()
    return Path(out) if out else start


def pick_base(root: Path, forced: str | None) -> str:
    if forced:
        return forced
    branch = git(["rev-parse", "--abbrev-ref", "HEAD"], root).strip()
    for main in ("main", "master"):
        if git(["rev-parse", "--verify", "--quiet", main], root).strip():
            if branch != main:
                mb = git(["merge-base", "HEAD", main], root).strip()
                if mb:
                    return mb
            break
    return "HEAD"


def changed_ranges(root: Path, base: str) -> dict[str, list[list[int]]]:
    """Changed line ranges per file: committed since base + uncommitted, plus untracked files."""
    out: dict[str, list[list[int]]] = {}
    diff = git(["diff", "-U0", "--no-color", "--no-ext-diff", base, "--"], root)
    current = None
    for line in diff.splitlines():
        if line.startswith("+++ "):
            path = line[4:].strip()
            current = None if path == "/dev/null" else path[2:] if path.startswith("b/") else path
            continue
        m = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", line)
        if m and current:
            start, count = int(m.group(1)), int(m.group(2) or 1)
            if count > 0:
                out.setdefault(current, []).append([start, start + count - 1])
    for path in git(["ls-files", "--others", "--exclude-standard"], root).splitlines():
        p = root / path
        if p.is_file():
            try:
                n = len(p.read_text(encoding="utf-8", errors="replace").splitlines())
            except OSError:
                continue
            if n:
                out[path] = [[1, n]]
    return out


def project_dir(root: Path, rel: str) -> Path:
    p = (root / rel).parent
    while True:
        if (p / "package.json").exists() or any((p / m).exists() for m in PY_MARKERS):
            return p
        if p == root or p.parent == p:
            return root
        p = p.parent


def interpreter(proj: Path, root: Path) -> str:
    for base in (proj, root):
        for venv in (".venv", "venv", "env"):
            for exe in ("Scripts/python.exe", "bin/python"):
                cand = base / venv / exe
                if cand.exists():
                    return str(cand)
    return sys.executable


def node_runner(proj: Path) -> tuple[str, str]:
    try:
        pkg = json.loads((proj / "package.json").read_text(encoding="utf-8"))
    except Exception:
        return "", ""
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    script = pkg.get("scripts", {}).get("test", "")
    if "vitest" in deps or "vitest" in script:
        return "vitest", "npx vitest run"
    if "jest" in deps or "jest" in script:
        return "jest", "npx jest"
    if "mocha" in deps:
        return "mocha", "npx mocha"
    if script and "no test specified" not in script:
        return "npm", "npm test --silent"
    if any((proj / d).exists() for d in ("test", "tests")):
        return "node", "node --test"
    return "", ""


def python_runner(proj: Path, py: str) -> tuple[str, str]:
    has_pytest_cfg = (proj / "pytest.ini").exists() or (proj / "conftest.py").exists() or (
        (proj / "pyproject.toml").exists()
        and "[tool.pytest" in (proj / "pyproject.toml").read_text(encoding="utf-8", errors="replace")
    )
    if (proj / "manage.py").exists() and not has_pytest_cfg:
        return "django", f'"{py}" manage.py test'
    return "pytest", f'"{py}" -m pytest -q -x'


def main(argv: list[str]) -> int:
    base_arg = None
    rest = []
    it = iter(argv)
    for a in it:
        if a == "--base":
            base_arg = next(it, None)
        else:
            rest.append(a)
    root = find_root(Path(rest[0]).resolve() if rest else Path.cwd())
    base = pick_base(root, base_arg)
    ranges = changed_ranges(root, base)

    projects: dict[Path, dict] = {}
    other: list[str] = []
    for rel, rngs in sorted(ranges.items()):
        ext = Path(rel).suffix
        if ext not in CODE_EXT or NON_LOGIC_RE.search(rel):
            other.append(rel)
            continue
        proj = project_dir(root, rel)
        info = projects.get(proj)
        if info is None:
            is_node = (proj / "package.json").exists() and ext in JS_EXT
            if ext in PY_EXT:
                py = interpreter(proj, root)
                runner, cmd = python_runner(proj, py)
                info = {"dir": str(proj), "stack": "python", "django": (proj / "manage.py").exists(),
                        "python": py, "runner": runner, "test_cmd": cmd}
            else:
                runner, cmd = node_runner(proj) if is_node else ("", "")
                info = {"dir": str(proj), "stack": "node", "django": False,
                        "python": None, "runner": runner, "test_cmd": cmd}
            info.update({"code": {}, "tests": {}, "logic_lines": 0})
            projects[proj] = info
        rel_proj = (root / rel).relative_to(proj).as_posix()
        if TEST_RE.search(rel):
            info["tests"][rel_proj] = rngs
        else:
            info["code"][rel_proj] = rngs
            info["logic_lines"] += sum(e - s + 1 for s, e in rngs)

    logic = sum(p["logic_lines"] for p in projects.values())
    print(json.dumps({
        "root": str(root),
        "base": base,
        "projects": list(projects.values()),
        "other": other,
        "logic_lines": logic,
        "small": logic < CONFIG["small_change_lines"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
