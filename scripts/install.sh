#!/usr/bin/env sh
set -eu

usage() {
  echo "Usage: $0 <skill> [all|codex|claude|gemini|grok|opencode|hermes] [--force]" >&2
  exit 2
}

[ "$#" -ge 1 ] || usage

skill=$1
target=${2:-all}
force=${3:-}

case "$skill" in
  *[!a-z0-9-]* | -* | *- | *--*) usage ;;
esac

case "$target" in
  all|codex|claude|gemini|grok|opencode|hermes) ;;
  *) usage ;;
esac

[ -z "$force" ] || [ "$force" = "--force" ] || usage

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(dirname -- "$script_dir")
source_dir="$repo_root/skills/$skill"
install_base=${SKILLS_BAR_HOME:-"$HOME"}

[ -f "$source_dir/SKILL.md" ] || {
  echo "Skill not found: $source_dir" >&2
  exit 1
}

install_to() {
  root=$1
  destination="$root/$skill"

  if [ -e "$destination" ]; then
    if [ "$force" != "--force" ]; then
      echo "Destination already exists: $destination. Re-run with --force to replace it." >&2
      exit 1
    fi
    rm -rf -- "$destination"
  fi

  mkdir -p -- "$root"
  cp -R -- "$source_dir" "$destination"
  echo "Installed $skill -> $destination"
}

case "$target" in
  all)
    install_to "$install_base/.agents/skills"
    install_to "$install_base/.claude/skills"
    install_to "$install_base/.hermes/skills"
    ;;
  codex|gemini|grok|opencode)
    install_to "$install_base/.agents/skills"
    ;;
  claude)
    install_to "$install_base/.claude/skills"
    ;;
  hermes)
    install_to "$install_base/.hermes/skills"
    ;;
esac
