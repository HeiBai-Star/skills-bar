"""Shared parsing and file rules for the repository's authoring tools."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
REPOSITORY = "HeiBai-Star/skills-bar"
BRANCH = "main"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VERSION_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?$")
FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", re.DOTALL)
IGNORED_DIRS = { "__pycache__", ".git", ".venv", ".pytest_cache", ".mypy_cache", ".ruff_cache" }
IGNORED_FILES = {".DS_Store", "Thumbs.db"}


class UniqueLoader(yaml.SafeLoader):
    """Reject duplicate mapping keys instead of silently taking the last one."""


def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise ValueError("YAML mapping keys must be strings")
        if key in result:
            raise ValueError(f"Duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def read_yaml(text: str):
    return yaml.load(text, Loader=UniqueLoader)


def frontmatter(path: Path) -> dict:
    match = FRONTMATTER_RE.match(path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError("Missing YAML frontmatter delimited by ---")
    data = read_yaml(match.group(1))
    if not isinstance(data, dict):
        raise ValueError("Frontmatter must be a YAML mapping")
    return data


def skill_directories(root: Path) -> list[Path]:
    skills = root / "skills"
    if not skills.is_dir():
        return []
    return sorted(p for p in skills.iterdir() if p.is_dir() and not p.name.startswith("."))


def ignored(path: Path, base: Path) -> bool:
    return bool(set(path.relative_to(base).parts) & IGNORED_DIRS) or (
        path.name in IGNORED_FILES or path.suffix in {".pyc", ".pyo"}
    )


def bundle_files(skill: Path) -> list[Path]:
    """One sorted file set drives hashes, validation and ZIP contents."""
    if skill.is_symlink():
        raise ValueError("Skill directory must not be a symlink")
    files = []
    # pathlib sorts Windows paths case-insensitively; use POSIX strings so a
    # mixed-case filename has the same position in Windows/macOS/Linux hashes.
    for path in sorted(skill.rglob("*"), key=lambda p: p.relative_to(skill).as_posix()):
        if ignored(path, skill):
            continue
        if path.is_symlink():
            raise ValueError(f"Symlinks are not portable: {path.relative_to(skill)}")
        if path.is_file():
            files.append(path)
    return files


def content_hash(skill: Path) -> str:
    entries = [
        [p.relative_to(skill).as_posix(), hashlib.sha256(p.read_bytes()).hexdigest()]
        for p in bundle_files(skill)
    ]
    canonical = json.dumps(entries, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def json_text(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"
