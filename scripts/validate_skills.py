#!/usr/bin/env python3
"""Validate repository skills against the portable Agent Skills subset."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path


NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", re.DOTALL)
TOP_KEY_RE = re.compile(r"^([A-Za-z0-9_-]+):(?:\s*(.*))?$")
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
ALLOWED_KEYS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}


def scalar(value: str) -> str:
    value = value.strip()
    if value.startswith(("'", '"')):
        try:
            parsed = ast.literal_eval(value)
        except (SyntaxError, ValueError):
            return value
        return parsed if isinstance(parsed, str) else value
    return value


def validate(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        return [f"{skill_dir}: missing SKILL.md"]

    text = skill_file.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return [f"{skill_file}: missing valid YAML frontmatter block"]

    values: dict[str, str] = {}
    keys: set[str] = set()
    for line_number, line in enumerate(match.group(1).splitlines(), start=2):
        if not line or line[0].isspace() or line.lstrip().startswith("#"):
            continue
        key_match = TOP_KEY_RE.match(line)
        if not key_match:
            errors.append(f"{skill_file}:{line_number}: invalid top-level frontmatter line")
            continue
        key, raw_value = key_match.groups()
        keys.add(key)
        values[key] = scalar(raw_value or "")

    unsupported = sorted(keys - ALLOWED_KEYS)
    if unsupported:
        errors.append(f"{skill_file}: non-portable frontmatter keys: {', '.join(unsupported)}")

    name = values.get("name", "")
    description = values.get("description", "")
    compatibility = values.get("compatibility", "")

    if not NAME_RE.fullmatch(name):
        errors.append(f"{skill_file}: invalid name: {name!r}")
    if name != skill_dir.name:
        errors.append(f"{skill_file}: name must match directory {skill_dir.name!r}")
    if not 1 <= len(description) <= 1024:
        errors.append(f"{skill_file}: description must contain 1-1024 characters")
    if compatibility and len(compatibility) > 500:
        errors.append(f"{skill_file}: compatibility must contain at most 500 characters")

    for target in LINK_RE.findall(text):
        target = target.strip().split("#", 1)[0]
        if not target or "://" in target or target.startswith(("#", "mailto:")):
            continue
        if not (skill_dir / target).resolve().is_file():
            errors.append(f"{skill_file}: missing referenced file: {target}")

    script_dir = skill_dir / "scripts"
    scripts = script_dir.glob("*.py") if script_dir.is_dir() else []
    for script in scripts:
        try:
            compile(script.read_text(encoding="utf-8"), str(script), "exec")
        except SyntaxError as exc:
            errors.append(f"{script}:{exc.lineno}: Python syntax error: {exc.msg}")

    return errors


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    skills_root = repo_root / "skills"
    skill_dirs = sorted(path for path in skills_root.iterdir() if path.is_dir())
    if not skill_dirs:
        print("No skills found", file=sys.stderr)
        return 1

    errors = [error for skill_dir in skill_dirs for error in validate(skill_dir)]
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print(f"Validated {len(skill_dirs)} portable skill(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
