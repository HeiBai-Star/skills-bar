#!/usr/bin/env python3
"""Generate registry, catalog and reproducible per-Skill ZIP archives."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
import zipfile
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote, urlencode

from skill_tools import ROOT, REPOSITORY, BRANCH, bundle_files, content_hash, frontmatter, json_text, skill_directories
from validate_skills import validate_repository

START = "<!-- skills-catalog:start -->"
END = "<!-- skills-catalog:end -->"


def records(root: Path) -> list[dict]:
    result = []
    for skill in skill_directories(root):
        data = frontmatter(skill / "SKILL.md")
        meta = data["metadata"]
        path = skill.relative_to(root).as_posix()
        result.append({
            "name": data["name"], "path": path,
            "description": data["description"],
            "summary": meta.get("short-description", data["description"]),
            "category": meta["category"], "version": meta["version"], "license": data["license"],
            "format": "agent-skills",
            "optional_runtime": meta.get("optional-runtime"),
            "content_sha256": content_hash(skill),
            "url": f"https://github.com/{REPOSITORY}/tree/{quote(BRANCH, safe='')}/{quote(path)}",
            "ccswitch_url": "ccswitch://v1/import?" + urlencode({
                "resource": "skill", "name": data["name"], "repo": REPOSITORY,
                "directory": path, "branch": BRANCH,
            }),
        })
    return result


def cell(value: str) -> str:
    return value.replace("|", "&#124;").replace("\n", " ").replace("\r", " ")


def generated_files(root: Path) -> dict[str, str]:
    skills = records(root)
    catalog = ["| Skill | 简介 | 版本 | 安装入口 |", "|---|---|---|---|"]
    for item in skills:
        name = item["name"]
        catalog.append(
            f"| [{name}]({item['path']}/SKILL.md) | {cell(item['summary'])} | "
            f"{item['version']} | [GitHub / 手机]({item['url']}) · "
            f"[CC Switch](docs/cc-switch-links.md#{name}) |"
        )
    readme = (root / "README.md").read_text(encoding="utf-8")
    if readme.count(START) != 1 or readme.count(END) != 1 or readme.index(START) > readme.index(END):
        raise ValueError("README needs exactly one ordered skills-catalog marker pair")
    block = START + "\n\n" + "\n".join(catalog) + "\n\n" + END
    readme = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, readme, flags=re.S)
    groupings = defaultdict(list)
    for item in skills:
        groupings[item["category"]].append(item["name"])
    links = [
        "# CC Switch 导入链接", "",
        "此文件自动生成。复制对应链接到支持自定义协议的浏览器或应用，在 CC Switch 中确认导入仓库，再选择安装技能。",
        "GitHub 的 Markdown 页面可能不允许直接点击 ccswitch:// 链接，因此保留可复制的完整文本。",
        "配置与版本差异见 [接入说明](cc-switch.md)。", "",
    ]
    for item in skills:
        links.extend([f"## {item['name']}", "", "~~~text", item["ccswitch_url"], "~~~", ""])
    return {
        "registry.json": json_text({
            "schema_version": 1, "name": "Skills Bar", "repository": REPOSITORY,
            "branch": BRANCH, "skills_root": "skills", "skills": skills,
        }),
        "skills.sh.json": json_text({
            "$schema": "https://skills.sh/schemas/skills.sh.schema.json",
            "groupings": [
                {"title": category.replace("-", " ").title(), "skills": names}
                for category, names in sorted(groupings.items())
            ],
        }),
        "docs/cc-switch-links.md": "\n".join(links),
        "README.md": readme,
    }


def package_skills(root: Path, output: Path) -> dict[str, str]:
    output = output.resolve()
    if output == root or output.is_relative_to(root / "skills") or output in root.parents:
        raise ValueError("ZIP output must be separate from the repository root and Skill sources")
    output.mkdir(parents=True, exist_ok=True)
    checksums = {}
    for item in records(root):
        skill = root / item["path"]
        payloads = {p.relative_to(skill).as_posix(): p.read_bytes() for p in bundle_files(skill)}
        if "LICENSE" not in payloads:
            if item["license"] != "MIT":
                raise ValueError(f"{item['name']}: non-MIT skill needs its own LICENSE for redistribution")
            payloads["LICENSE"] = (root / "LICENSE").read_bytes()
        filename = f"{item['name']}-{item['version']}.zip"
        with zipfile.ZipFile(output / filename, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path, data in sorted(payloads.items()):
                info = zipfile.ZipInfo(f"{item['name']}/{path}", date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                mode = 0o100755 if path.endswith(".sh") else 0o100644
                info.external_attr = mode << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, data)
        checksums[filename] = hashlib.sha256((output / filename).read_bytes()).hexdigest()
    (output / "checksums.json").write_text(json_text(checksums), encoding="utf-8", newline="\n")
    return checksums


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true", help="Fail on stale generated files without writing")
    parser.add_argument("--package", action="store_true", help="Also write per-Skill ZIP files")
    parser.add_argument("--output", type=Path, help="ZIP directory; default: <repo>/dist")
    args = parser.parse_args()
    if args.check and args.package:
        parser.error("--check cannot be combined with --package")
    root = args.root.resolve()
    errors = validate_repository(root)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    try:
        stale = []
        for relative, expected in generated_files(root).items():
            path = root / relative
            if not path.exists() or path.read_text(encoding="utf-8") != expected:
                stale.append(relative)
                if not args.check:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(expected, encoding="utf-8", newline="\n")
        if args.check and stale:
            print("Stale generated files: " + ", ".join(stale), file=sys.stderr)
            print("Run: python scripts/build_skills.py", file=sys.stderr)
            return 1
        if args.package:
            packages = package_skills(root, args.output or root / "dist")
            print(f"Built {len(packages)} ZIP(s) with checksums.")
    except (ValueError, OSError) as exc:
        print(f"Build failed: {exc}", file=sys.stderr)
        return 1
    print("Generated registry and catalog are current.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
