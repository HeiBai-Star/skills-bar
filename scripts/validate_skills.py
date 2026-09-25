#!/usr/bin/env python3
"""Validate portable skills and common accidental publication mistakes."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml

from skill_tools import ROOT, NAME_RE, VERSION_RE, bundle_files, frontmatter, read_yaml, skill_directories

# Conservative subset also accepted by the bundled Codex validator.
ALLOWED_KEYS = {"name", "description", "license", "metadata", "allowed-tools"}
LINK_RE = re.compile(r'!?\[[^\]]*\]\((<[^>]+>|[^\s)]+)(?:\s+"[^"]*")?\)')
DRAFT_RE = re.compile(r"\[TODO\b|\{\{[a-z_]+\}\}")
PERSONAL_PATH_RE = re.compile(r"[A-Za-z]:[\\/]+(?:Users|codex)[\\/]+|/(?:Users|home)/[A-Za-z0-9_.-]+/")
SECRET_RULES = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b"),
    "API token": re.compile(r"\bsk-(?:proj-|ant-api\d{2}-)?[A-Za-z0-9_-]{32,}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "credential in URL": re.compile(r"https?://[^\s/:@]+:[^\s/@]+@"),
}


def scan_text(text: str, label: str, personal_paths=False) -> list[str]:
    errors = []
    for line_number, line in enumerate(text.splitlines(), 1):
        for rule, pattern in SECRET_RULES.items():
            if pattern.search(line):
                # Never print the matching credential into logs.
                errors.append(f"{label}:{line_number}: possible {rule}")
        if personal_paths and PERSONAL_PATH_RE.search(line):
            errors.append(f"{label}:{line_number}: hard-coded personal filesystem path")
    return errors


def validate(skill: Path) -> list[str]:
    errors = []
    entry = skill / "SKILL.md"
    try:
        entry_text = entry.read_text(encoding="utf-8")
        publication_errors = scan_text(entry_text, str(entry), personal_paths=True)
        if publication_errors:
            return publication_errors
        data = frontmatter(entry)
        files = bundle_files(skill)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return [f"{entry}: {exc}"]

    extra = set(data) - ALLOWED_KEYS
    if extra:
        errors.append(f"{entry}: unsupported portable fields: {', '.join(sorted(extra))}")
    name = data.get("name")
    if not isinstance(name, str) or not NAME_RE.fullmatch(name) or len(name) > 64:
        errors.append(f"{entry}: name must be a 1-64 character lowercase hyphenated slug")
    if name != skill.name:
        errors.append(f"{entry}: name must match its directory")
    description = data.get("description")
    if not isinstance(description, str) or not 1 <= len(description.strip()) <= 1024:
        errors.append(f"{entry}: description must be a nonempty string of at most 1024 characters")
    if not isinstance(data.get("license"), str) or not data["license"].strip():
        errors.append(f"{entry}: declare a license for this repository's published skills")
    meta = data.get("metadata", {})
    if not isinstance(meta, dict) or any(not isinstance(v, str) for v in meta.values()):
        errors.append(f"{entry}: metadata must map strings to strings")
    else:
        if not VERSION_RE.fullmatch(meta.get("version", "")):
            errors.append(f"{entry}: metadata.version must be a quoted x.y.z version")
        if not NAME_RE.fullmatch(meta.get("category", "")):
            errors.append(f"{entry}: metadata.category must be a lowercase hyphenated slug")

    for path in files:
        label = f"{skill.name}/{path.relative_to(skill).as_posix()}"
        if path.name.startswith(".env") or path.name in {"id_rsa", "id_ed25519"}:
            errors.append(f"{label}: local credential/config file must not be bundled")
        if path.name == "SKILL.md" and path != entry:
            errors.append(f"{label}: nested Skill entrypoints are not supported")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue  # Binary assets are allowed; secret checks are text-only.
        publication_errors = scan_text(text, label, personal_paths=True)
        errors.extend(publication_errors)
        if publication_errors:
            # YAML parsers and link errors can quote source text; do not pass
            # secret-bearing text to diagnostics that would expose it.
            continue
        if DRAFT_RE.search(text):
            errors.append(f"{label}: unfinished template placeholder")
        if path.suffix == ".py":
            try:
                compile(text, str(path), "exec")
            except SyntaxError as exc:
                errors.append(f"{label}:{exc.lineno}: invalid Python: {exc.msg}")
        if path.suffix in {".yaml", ".yml"}:
            try:
                read_yaml(text)
            except (ValueError, yaml.YAMLError) as exc:
                errors.append(f"{label}: invalid YAML: {exc}")
        if path.suffix == ".md":
            for raw in LINK_RE.findall(text):
                target = unquote(raw.strip("<>"))
                parsed = urlsplit(target)
                if parsed.scheme or target.startswith("#"):
                    continue
                dest = (path.parent / parsed.path).resolve()
                if not dest.is_relative_to(skill.resolve()):
                    errors.append(f"{label}: reference escapes the Skill directory: {target}")
                elif not dest.exists():
                    errors.append(f"{label}: missing reference: {target}")
    return errors


def validate_repository(root: Path) -> list[str]:
    skills = skill_directories(root)
    errors = [] if skills else ["No skills found under skills/"]
    for skill in skills:
        errors.extend(validate(skill))
    if (root / "skills").is_dir():
        for entry in (root / "skills").iterdir():
            if not entry.is_dir():
                errors.append(f"{entry}: only independent Skill directories belong in skills/")

    # Include tracked files even if an ignore rule was subsequently added.
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root, capture_output=True, check=False,
    )
    if result.returncode:
        errors.append("Repository publication scan requires a Git working tree")
        return errors
    paths = sorted(set(result.stdout.decode("utf-8").split("\0")) - {""})
    for relative in paths:
        path = root / relative
        if not path.is_file():
            continue
        if path.name == "SKILL.md" and not relative.startswith("skills/"):
            errors.append(f"{relative}: discoverable Skill outside skills/; use .tmpl for templates")
        if path.name.startswith(".env") and path.name != ".env.example":
            errors.append(f"{relative}: environment file must not be published")
        try:
            errors.extend(scan_text(path.read_text(encoding="utf-8"), relative))
        except UnicodeDecodeError:
            pass
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    errors = validate_repository(args.root.resolve())
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Validated {len(skill_directories(args.root))} skill(s), references, scripts and publication checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
