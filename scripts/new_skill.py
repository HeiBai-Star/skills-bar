#!/usr/bin/env python3
"""Create an unpublished Skill draft from the repository template."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from skill_tools import ROOT, NAME_RE


def create_skill(root: Path, name: str, description: str, title: str, category: str) -> Path:
    if not NAME_RE.fullmatch(name) or len(name) > 64:
        raise ValueError("Name must be a lowercase hyphenated slug of at most 64 characters")
    if not NAME_RE.fullmatch(category):
        raise ValueError("Category must be a lowercase hyphenated slug")
    if not 1 <= len(description.strip()) <= 1024:
        raise ValueError("Description must contain 1-1024 characters")
    if not title.strip() or "\n" in title or "\r" in title:
        raise ValueError("Title must be a nonempty single line")
    values = {
        "name": name, "title": title,
        "title_yaml": json.dumps(title, ensure_ascii=False),
        "description_yaml": json.dumps(description, ensure_ascii=False),
        "category_yaml": json.dumps(category, ensure_ascii=False),
        "ui_description_yaml": json.dumps(description[:64], ensure_ascii=False),
        "prompt_yaml": json.dumps("使用 $" + name + " 完成我的任务，并检查交付结果。", ensure_ascii=False),
    }
    template = root / "templates" / "skill-template"
    rendered = {}
    for path in sorted(template.rglob("*.tmpl")):
        relative = Path(str(path.relative_to(template))[:-5])
        rendered[relative] = re.sub(
            r"\{\{([a-z_]+)\}\}", lambda m: values[m.group(1)], path.read_text(encoding="utf-8")
        )
    if Path("SKILL.md") not in rendered:
        raise ValueError("Missing SKILL.md.tmpl")
    destination = root / "skills" / name
    destination.mkdir(parents=True, exist_ok=False)
    for relative, text in rendered.items():
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name")
    parser.add_argument("--description", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--category", default="general")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        path = create_skill(args.root.resolve(), args.name, args.description, args.title, args.category)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Cannot create Skill: {exc}\n")
    print(f"Draft created: {path}")
    print("Replace every [TODO] placeholder, then validate and regenerate the catalog before committing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
