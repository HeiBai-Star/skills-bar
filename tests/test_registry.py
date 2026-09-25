"""Behavioral tests for authoring, validation, generated indexes and archives."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_skills import generated_files, package_skills, records
from new_skill import create_skill
from skill_tools import bundle_files, content_hash, frontmatter
from validate_skills import scan_text, validate, validate_repository


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="skills-bar-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        shutil.copytree(ROOT / "templates", self.root / "templates")
        shutil.copyfile(ROOT / "LICENSE", self.root / "LICENSE")
        (self.root / "README.md").write_text(
            "# Example\n\n<!-- skills-catalog:start -->\n<!-- skills-catalog:end -->\n",
            encoding="utf-8",
        )
        self.skill = create_skill(
            self.root, "test-skill", '处理 "引号": 输入\n并检查结果。',
            "测试技能", "testing",
        )
        entry = self.skill / "SKILL.md"
        self.draft = entry.read_text(encoding="utf-8")
        entry.write_text(
            self.draft[:self.draft.index("\n# ")] + "\n# Ready\n\nDeliver the requested result.\n",
            encoding="utf-8", newline="\n",
        )

    def test_template_creates_valid_metadata_but_unfinished_draft_is_rejected(self):
        entry = self.skill / "SKILL.md"
        self.assertEqual(frontmatter(entry)["description"], '处理 "引号": 输入\n并检查结果。')
        self.assertEqual(validate(self.skill), [])
        entry.write_text(self.draft, encoding="utf-8")
        self.assertTrue(any("placeholder" in error for error in validate(self.skill)))
        self.assertFalse(list((self.root / "templates").rglob("SKILL.md")))
        with self.assertRaises(FileExistsError):
            create_skill(self.root, "test-skill", "description", "Title", "testing")
        with self.assertRaises(ValueError):
            create_skill(self.root, "../escape", "description", "Title", "testing")

    def test_duplicate_keys_types_and_multiline_yaml(self):
        entry = self.skill / "SKILL.md"
        text = entry.read_text(encoding="utf-8")
        entry.write_text(text.replace("name: test-skill", "name: test-skill\nname: other"), encoding="utf-8")
        self.assertTrue(any("Duplicate YAML key" in error for error in validate(self.skill)))
        entry.write_text(text.replace('version: "0.1.0"', "version: 1"), encoding="utf-8")
        self.assertTrue(any("metadata must" in error for error in validate(self.skill)))
        entry.write_text(
            text.replace('description: "处理 \\"引号\\": 输入\\n并检查结果。"', "description: >\n  First line\n  second line"),
            encoding="utf-8",
        )
        self.assertEqual(frontmatter(entry)["description"], "First line second line\n")
        self.assertEqual(validate(self.skill), [])

    def test_missing_and_escaping_references_are_rejected(self):
        entry = self.skill / "SKILL.md"
        text = entry.read_text(encoding="utf-8")
        entry.write_text(text + "\n[missing](references/missing.md)\n", encoding="utf-8")
        self.assertTrue(any("missing reference" in error for error in validate(self.skill)))
        entry.write_text(text + "\n[outside](../../LICENSE)\n", encoding="utf-8")
        self.assertTrue(any("escapes" in error for error in validate(self.skill)))

    def test_nested_resources_change_hash_caches_do_not(self):
        before = content_hash(self.skill)
        references = self.skill / "references"
        references.mkdir()
        (references / "guide.md").write_text("Useful guidance", encoding="utf-8")
        after = content_hash(self.skill)
        self.assertNotEqual(before, after)
        cache = self.skill / "__pycache__"
        cache.mkdir()
        (cache / "helper.pyc").write_bytes(b"ignored")
        self.assertEqual(after, content_hash(self.skill))
        (references / "guide.md").write_text("[bad](missing.md)", encoding="utf-8")
        self.assertTrue(any("missing reference" in error for error in validate(self.skill)))

    def test_bundle_order_is_case_sensitive_on_every_platform(self):
        (self.skill / "Z.txt").write_text("upper", encoding="utf-8")
        (self.skill / "a.txt").write_text("lower", encoding="utf-8")
        paths = [p.relative_to(self.skill).as_posix() for p in bundle_files(self.skill)]
        self.assertEqual(paths, ["SKILL.md", "Z.txt", "a.txt", "agents/openai.yaml"])

    def test_publication_scan_rejects_credential_without_logging_it(self):
        token = "ghp_" + "A" * 36
        errors = scan_text(token, "example.md")
        self.assertTrue(errors)
        self.assertNotIn(token, "\n".join(errors))
        entry = self.skill / "SKILL.md"
        original = entry.read_text(encoding="utf-8")
        entry.write_text(original.replace("license: MIT", "license: [" + token), encoding="utf-8")
        self.assertNotIn(token, "\n".join(validate(self.skill)))
        entry.write_text(original, encoding="utf-8")
        personal_path = "C:" + "/" + "Users" + "/example/work"
        self.assertTrue(scan_text(personal_path, "SKILL.md", personal_paths=True))
        (self.root / "leak.txt").write_text(token, encoding="utf-8")
        self.assertTrue(any("GitHub token" in error for error in validate_repository(self.root)))
        (self.root / "templates" / "SKILL.md").write_text("Not a real skill", encoding="utf-8")
        self.assertTrue(any("outside skills/" in error for error in validate_repository(self.root)))

    def test_catalog_and_deeplink_only_describe_published_skills(self):
        self.assertEqual(validate_repository(self.root), [])
        result = records(self.root)
        self.assertEqual([item["name"] for item in result], ["test-skill"])
        query = parse_qs(urlsplit(result[0]["ccswitch_url"]).query)
        self.assertEqual(query["directory"], ["skills/test-skill"])
        self.assertEqual(query["repo"], ["HeiBai-Star/skills-bar"])
        self.assertEqual(query["branch"], ["main"])
        self.assertEqual(query["resource"], ["skill"])
        generated = generated_files(self.root)
        for relative, expected in generated.items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8", newline="\n")
        self.assertEqual(generated_files(self.root), generated)

        command = [sys.executable, str(ROOT / "scripts" / "build_skills.py"), "--root", str(self.root), "--check"]
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
        entry = self.skill / "SKILL.md"
        entry.write_text(entry.read_text(encoding="utf-8") + "\nNew guidance.\n", encoding="utf-8")
        self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)

    def test_zip_includes_resources_and_license_and_is_reproducible(self):
        scripts = self.skill / "scripts"
        scripts.mkdir()
        (scripts / "helper.py").write_text("print('ready')\n", encoding="utf-8", newline="\n")
        first = package_skills(self.root, self.root / "dist")
        archive_path = self.root / "dist" / "test-skill-0.1.0.zip"
        first_bytes = archive_path.read_bytes()
        with zipfile.ZipFile(archive_path) as archive:
            self.assertIn("test-skill/SKILL.md", archive.namelist())
            self.assertIn("test-skill/scripts/helper.py", archive.namelist())
            self.assertIn("test-skill/LICENSE", archive.namelist())
            self.assertEqual(archive.read("test-skill/scripts/helper.py"), b"print('ready')\n")
            self.assertFalse(any("templates/" in name for name in archive.namelist()))
        second = package_skills(self.root, self.root / "dist")
        self.assertEqual(first, second)
        self.assertEqual(first_bytes, archive_path.read_bytes())
        self.assertEqual(first[archive_path.name], hashlib.sha256(first_bytes).hexdigest())
        with self.assertRaises(ValueError):
            package_skills(self.root, self.root / "skills")
        with self.assertRaises(ValueError):
            package_skills(self.root / "skills" / "..", self.root / "skills")

    @unittest.skipIf(os.name == "nt", "POSIX shell installer runs on Linux/macOS CI")
    def test_posix_installer_copies_resources_and_refuses_implicit_overwrite(self):
        destination = self.root / "install-home"
        env = dict(os.environ, SKILLS_BAR_HOME=str(destination))
        command = ["sh", str(ROOT / "scripts" / "install.sh"), "decision-model-builder", "all"]
        self.assertEqual(subprocess.run(command, env=env, capture_output=True).returncode, 0)
        for client in (".agents", ".claude", ".hermes"):
            installed = destination / client / "skills" / "decision-model-builder"
            self.assertTrue((installed / "SKILL.md").is_file())
            self.assertTrue((installed / "scripts" / "score_options.py").is_file())
        self.assertNotEqual(subprocess.run(command, env=env, capture_output=True).returncode, 0)


if __name__ == "__main__":
    unittest.main()
