from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FIELDS = [
    "slug",
    "title",
    "summary",
    "origin_note",
    "collection_path",
    "lifecycle",
    "sync_status",
    "guide_path",
    "license",
    "tags",
    "updated_at",
]

KNOWN_LIFECYCLES = {"active", "experimental", "deprecated", "retired"}
KNOWN_SYNC_STATUSES = {"staged", "published", "draft", "local"}
KNOWN_LICENSES = {"MIT", "Apache-2.0", "CC0-1.0", "BSD-3-Clause"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class RegistryConsistencyTest(unittest.TestCase):
    def test_registry_entries_point_to_existing_skill_files(self) -> None:
        registry = json.loads((ROOT / "registry" / "skills.json").read_text(encoding="utf-8"))
        slugs = set()

        for skill in registry["skills"]:
            with self.subTest(slug=skill["slug"]):
                slugs.add(skill["slug"])
                collection_path = ROOT / skill["collection_path"]
                guide_path = ROOT / skill["guide_path"]

                self.assertTrue(collection_path.is_dir(), f"missing collection_path: {collection_path}")
                self.assertTrue((collection_path / "SKILL.md").is_file(), f"missing SKILL.md for {skill['slug']}")
                self.assertTrue(guide_path.is_file(), f"missing guide_path: {guide_path}")

        skill_dirs = {path.name for path in (ROOT / "skills").iterdir() if path.is_dir()}
        self.assertEqual(slugs, skill_dirs)

    def test_registry_entries_have_required_fields(self) -> None:
        registry = json.loads((ROOT / "registry" / "skills.json").read_text(encoding="utf-8"))
        for skill in registry["skills"]:
            with self.subTest(slug=skill.get("slug", "<missing>")):
                for field in REQUIRED_FIELDS:
                    self.assertIn(field, skill, f"missing field: {field}")
                    self.assertTrue(
                        skill[field] or skill[field] in (True, False, 0),
                        f"field {field} is empty",
                    )

    def test_registry_tags_are_non_empty_lists(self) -> None:
        registry = json.loads((ROOT / "registry" / "skills.json").read_text(encoding="utf-8"))
        for skill in registry["skills"]:
            with self.subTest(slug=skill["slug"]):
                tags = skill["tags"]
                self.assertIsInstance(tags, list, "tags must be a list")
                self.assertGreater(len(tags), 0, "tags must not be empty")
                for tag in tags:
                    self.assertIsInstance(tag, str, f"tag must be a string: {tag}")
                    self.assertTrue(tag.strip(), f"tag must not be blank: {tag!r}")

    def test_registry_updated_at_is_valid_date(self) -> None:
        registry = json.loads((ROOT / "registry" / "skills.json").read_text(encoding="utf-8"))
        for skill in registry["skills"]:
            with self.subTest(slug=skill["slug"]):
                self.assertRegex(
                    skill["updated_at"],
                    DATE_RE,
                    f"updated_at must be YYYY-MM-DD: {skill['updated_at']!r}",
                )

    def test_registry_enum_fields_have_known_values(self) -> None:
        registry = json.loads((ROOT / "registry" / "skills.json").read_text(encoding="utf-8"))
        for skill in registry["skills"]:
            with self.subTest(slug=skill["slug"]):
                self.assertIn(
                    skill["lifecycle"],
                    KNOWN_LIFECYCLES,
                    f"unknown lifecycle: {skill['lifecycle']!r}",
                )
                self.assertIn(
                    skill["sync_status"],
                    KNOWN_SYNC_STATUSES,
                    f"unknown sync_status: {skill['sync_status']!r}",
                )
                self.assertIn(
                    skill["license"],
                    KNOWN_LICENSES,
                    f"unknown license: {skill['license']!r}",
                )

    def test_registry_paths_follow_convention(self) -> None:
        registry = json.loads((ROOT / "registry" / "skills.json").read_text(encoding="utf-8"))
        for skill in registry["skills"]:
            slug = skill["slug"]
            with self.subTest(slug=slug):
                self.assertEqual(
                    skill["collection_path"],
                    f"skills/{slug}",
                    f"collection_path must be skills/<slug>",
                )
                self.assertEqual(
                    skill["guide_path"],
                    f"docs/skills/{slug}.md",
                    f"guide_path must be docs/skills/<slug>.md",
                )

    def test_registry_slugs_are_unique(self) -> None:
        registry = json.loads((ROOT / "registry" / "skills.json").read_text(encoding="utf-8"))
        slugs = [skill["slug"] for skill in registry["skills"]]
        self.assertEqual(len(slugs), len(set(slugs)), "duplicate slugs found")

    def test_registry_top_level_fields(self) -> None:
        registry = json.loads((ROOT / "registry" / "skills.json").read_text(encoding="utf-8"))
        self.assertEqual(registry["repo_name"], "chris-open-skills")
        self.assertIn("updated_at", registry)
        self.assertIn("skills", registry)
        self.assertIsInstance(registry["skills"], list)
        self.assertGreater(len(registry["skills"]), 0)


if __name__ == "__main__":
    unittest.main()
