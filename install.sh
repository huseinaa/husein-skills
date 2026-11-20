#!/usr/bin/env bash
# Links skills from this repo into ~/.claude/skills, so a `git pull` updates them.
#   ./install.sh                      all skills
#   ./install.sh reel-edit            one skill
#   ./install.sh reel-edit feature-testing
set -euo pipefail

src="$(cd "$(dirname "$0")" && pwd)/skills"
dst="$HOME/.claude/skills"
mkdir -p "$dst"

available=()
for d in "$src"/*/; do
  [ -f "$d/SKILL.md" ] && available+=("$(basename "$d")")
done

if [ "$#" -eq 0 ]; then set -- "${available[@]}"; fi

for name in "$@"; do
  if [ ! -f "$src/$name/SKILL.md" ]; then
    echo "SKIP  $name  (no such skill; available: ${available[*]})"
    continue
  fi
  link="$dst/$name"
  if [ -L "$link" ]; then
    rm "$link"
  elif [ -e "$link" ]; then
    echo "SKIP  $name  ($link is a real folder; move or delete it first, then run again)"
    continue
  fi
  ln -s "$src/$name" "$link"
  echo "OK    $name  ->  $src/$name"
done

echo
echo "Done. Open a new Claude Code session and type / to see the skills."
