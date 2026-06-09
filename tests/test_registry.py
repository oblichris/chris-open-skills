from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


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


if __name__ == "__main__":
    unittest.main()
