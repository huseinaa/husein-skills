"""Insert, update or remove the /feature-testing block in a repo's CLAUDE.md / AGENTS.md.

Usage:
    python install_rule.py [repo_dir]            install or update (idempotent)
    python install_rule.py [repo_dir] --check    exit 0 if installed, 1 if not
    python install_rule.py [repo_dir] --remove   take the block out
    python install_rule.py [repo_dir] --force    install even without a project file at the root

Rules:
- Writes to AGENTS.md if it exists and to CLAUDE.md if it exists.
- Creates CLAUDE.md only when neither exists.
- Refuses when the repo root has no project file (package.json, pyproject.toml, manage.py...).
  --force adds it anyway.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

START = "<!-- feature-testing:start -->"
END = "<!-- feature-testing:end -->"
BLOCK_RE = re.compile(re.escape(START) + r".*?" + re.escape(END) + r"\n?", re.S)

SKILL_DIR = Path(__file__).resolve().parent.parent
PROJECT_MARKERS = (
    "package.json", "pyproject.toml", "requirements.txt", "setup.py", "setup.cfg",
    "manage.py", "go.mod", "Cargo.toml", "pom.xml", "build.gradle", "composer.json", "Gemfile",
)


def repo_root(start: Path) -> Path:
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=start,
                             capture_output=True, text=True, check=True).stdout.strip()
        return Path(out)
    except Exception:
        return start


def is_code_repo(root: Path) -> bool:
    """A software project has a project file at its root. Notes repos with a few helper scripts do not."""
    return any((root / m).exists() for m in PROJECT_MARKERS)


def block_text() -> str:
    body = (SKILL_DIR / "rule-block.md").read_text(encoding="utf-8").strip()
    return f"{START}\n{body}\n{END}\n"


def targets(root: Path) -> list[Path]:
    found = [root / n for n in ("AGENTS.md", "CLAUDE.md") if (root / n).exists()]
    return found or [root / "CLAUDE.md"]


def read(path: Path) -> tuple[str, str]:
    """Text with \\n line endings, plus the file's own line ending so writing it back keeps it."""
    raw = path.read_bytes().decode("utf-8")
    eol = "\r\n" if "\r\n" in raw else "\n"
    return raw.replace("\r\n", "\n"), eol


def write(path: Path, text: str, eol: str) -> None:
    path.write_bytes(text.replace("\n", eol).encode("utf-8"))


def install(path: Path, block: str) -> str:
    if not path.exists():
        write(path, block, "\n")
        return "created"
    text, eol = read(path)
    if START in text:
        new = BLOCK_RE.sub(lambda _: block, text, count=1)
        if new == text:
            return "unchanged"
        write(path, new, eol)
        return "updated"
    sep = "" if text.endswith("\n\n") else ("\n" if text.endswith("\n") else "\n\n")
    write(path, text + sep + block, eol)
    return "added"


def remove(path: Path) -> str:
    if not path.exists():
        return "absent"
    text, eol = read(path)
    if START not in text:
        return "absent"
    write(path, BLOCK_RE.sub("", text).rstrip() + "\n", eol)
    return "removed"


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    flags = {a for a in argv if a.startswith("--")}
    root = repo_root(Path(args[0]).resolve() if args else Path.cwd())

    if "--remove" in flags:
        for p in (root / "AGENTS.md", root / "CLAUDE.md"):
            print(f"{p.name}: {remove(p)}")
        return 0

    if "--check" in flags:
        installed = any(p.exists() and START in p.read_text(encoding="utf-8")
                        for p in (root / "AGENTS.md", root / "CLAUDE.md"))
        print("installed" if installed else "not installed")
        return 0 if installed else 1

    if not is_code_repo(root) and "--force" not in flags:
        print(f"skipped: {root} has no project file at its root (package.json, pyproject.toml, manage.py...), "
              "so the rule was not added. Pass --force to add it anyway.")
        return 2

    block = block_text()
    for p in targets(root):
        print(f"{p.name}: {install(p, block)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
