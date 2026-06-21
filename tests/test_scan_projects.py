from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "skills" / "project-wip-auditor" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import scan_projects  # noqa: E402
from scan_projects import (  # noqa: E402
    DEFAULT_IGNORE_DIRS,
    GENERATED_DIRS,
    in_generated_path,
    iso_date,
    scan_project,
    scan_root,
)


def _touch(path: Path, mtime: float):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x", encoding="utf-8")
    os.utime(path, (mtime, mtime))


class TestIsoDate(unittest.TestCase):
    def test_none_returns_none(self):
        self.assertIsNone(iso_date(None))

    def test_zero_treated_as_missing(self):
        # newest_* start at 0.0; an empty project must yield None, not epoch.
        self.assertIsNone(iso_date(0))

    def test_known_timestamp(self):
        ts = datetime(2026, 6, 14, 12, 0, 0, tzinfo=timezone.utc).timestamp()
        self.assertEqual(iso_date(ts), "2026-06-14")

    def test_truncates_to_date_only(self):
        ts = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc).timestamp()
        self.assertEqual(iso_date(ts), "2026-01-02")


class TestInGeneratedPath(unittest.TestCase):
    def test_top_level_generated_dir(self):
        root = Path("/root")
        self.assertTrue(in_generated_path(root / "exports" / "big.png", root))

    def test_nested_generated_dir(self):
        root = Path("/root")
        self.assertTrue(in_generated_path(root / "outputs" / "reports" / "x.csv", root))

    def test_normal_source_dir(self):
        root = Path("/root")
        self.assertFalse(in_generated_path(root / "src" / "main.py", root))

    def test_file_directly_in_root(self):
        root = Path("/root")
        self.assertFalse(in_generated_path(root / "notes.txt", root))

    def test_case_insensitive(self):
        root = Path("/root")
        self.assertTrue(in_generated_path(root / "Exports" / "a.png", root))

    def test_all_generated_dirs_flagged(self):
        root = Path("/root")
        for name in GENERATED_DIRS:
            with self.subTest(dir=name):
                self.assertTrue(
                    in_generated_path(root / name / "f.bin", root),
                    msg=f"{name} should be detected as a generated path",
                )


class TestScanProject(unittest.TestCase):
    def _scan(self, builder, ignore=None):
        ignore = ignore if ignore is not None else set(DEFAULT_IGNORE_DIRS)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            builder(root)
            return scan_project(root, ignore)

    def test_counts_and_classification(self):
        t0 = 1_000_000_000.0

        def build(root):
            _touch(root / "README.md", t0)
            _touch(root / "src" / "app.py", t0)
            _touch(root / "src" / "logic.py", t0 + 100)
            _touch(root / "exports" / "screenshot.png", t0 + 200)

        result = self._scan(build)
        self.assertEqual(result["file_count"], 4)
        self.assertEqual(result["meaningful_file_count"], 3)
        self.assertEqual(result["noisy_file_count"], 1)
        self.assertTrue(result["has_readme"])
        self.assertFalse(result["has_todo"])
        self.assertFalse(result["is_git"])

    def test_newest_paths_split_meaningful_and_noise(self):
        t0 = 1_000_000_000.0

        def build(root):
            _touch(root / "README.md", t0)
            _touch(root / "src" / "app.py", t0)
            _touch(root / "src" / "logic.py", t0 + 100)
            _touch(root / "exports" / "screenshot.png", t0 + 200)

        result = self._scan(build)
        self.assertTrue(result["newest_mtime_path"].endswith("screenshot.png"))
        self.assertTrue(result["meaningful_mtime_path"].endswith("logic.py"))
        self.assertTrue(result["noise_mtime_path"].endswith("screenshot.png"))
        self.assertEqual(result["meaningful_mtime"], "2001-09-09")
        self.assertEqual(result["newest_mtime"], "2001-09-09")

    def test_source_file_in_generated_dir_is_noisy(self):
        # A .py file living under exports/ is generated, so it must count as
        # noise rather than meaningful work.
        t0 = 1_000_000_000.0

        def build(root):
            _touch(root / "exports" / "gen.py", t0)

        result = self._scan(build)
        self.assertEqual(result["meaningful_file_count"], 0)
        self.assertEqual(result["noisy_file_count"], 1)

    def test_todo_detected_by_name_and_token(self):
        t0 = 1_000_000_000.0

        def build(root):
            _touch(root / "TODO.md", t0)

        self.assertTrue(self._scan(build)["has_todo"])

    def test_todo_token_in_filename(self):
        t0 = 1_000_000_000.0

        def build(root):
            _touch(root / "project-todo.txt", t0)

        self.assertTrue(self._scan(build)["has_todo"])

    def test_readme_variants(self):
        t0 = 1_000_000_000.0

        def build(root):
            _touch(root / "AGENTS.md", t0)
            _touch(root / "CLAUDE.md", t0)

        result = self._scan(build)
        self.assertTrue(result["has_readme"])
        self.assertEqual(len(result["readme_paths"]), 2)

    def test_dotfiles_and_ds_store_ignored(self):
        t0 = 1_000_000_000.0

        def build(root):
            _touch(root / ".secret", t0)
            _touch(root / ".DS_Store", t0)
            _touch(root / "real.py", t0)

        result = self._scan(build)
        self.assertEqual(result["file_count"], 1)

    def test_ignore_dirs_pruned_from_walk(self):
        t0 = 1_000_000_000.0

        def build(root):
            _touch(root / "node_modules" / "dep.js", t0)
            _touch(root / "src" / "main.py", t0)

        result = self._scan(build)
        self.assertEqual(result["file_count"], 1)

    def test_hidden_subdir_skipped(self):
        t0 = 1_000_000_000.0

        def build(root):
            _touch(root / ".venv" / "lib.py", t0)
            _touch(root / "app.py", t0)

        result = self._scan(build)
        self.assertEqual(result["file_count"], 1)

    def test_empty_project_signals(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = scan_project(Path(tmp), set(DEFAULT_IGNORE_DIRS))
        self.assertEqual(result["file_count"], 0)
        self.assertIsNone(result["newest_mtime"])
        self.assertIsNone(result["meaningful_mtime"])
        self.assertIsNone(result["noise_mtime"])
        self.assertFalse(result["has_readme"])
        self.assertFalse(result["is_git"])

    def test_name_and_path_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "my-project"
            root.mkdir()
            result = scan_project(root, set(DEFAULT_IGNORE_DIRS))
        self.assertEqual(result["name"], "my-project")
        self.assertEqual(result["path"], str(root))


class TestScanRoot(unittest.TestCase):
    def test_enumerates_immediate_subdirs(self):
        t0 = 1_000_000_000.0
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root / "alpha" / "main.py", t0)
            _touch(root / "beta" / "app.py", t0)
            projects = scan_root(root, set(DEFAULT_IGNORE_DIRS))
        names = [p["name"] for p in projects]
        self.assertEqual(names, ["alpha", "beta"])

    def test_skips_dotdir_children(self):
        t0 = 1_000_000_000.0
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root / ".config" / "x.py", t0)
            _touch(root / "real" / "app.py", t0)
            projects = scan_root(root, set(DEFAULT_IGNORE_DIRS))
        self.assertEqual([p["name"] for p in projects], ["real"])

    def test_ignores_files_at_root(self):
        t0 = 1_000_000_000.0
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root / "loose-file.py", t0)
            projects = scan_root(root, set(DEFAULT_IGNORE_DIRS))
        self.assertEqual(projects, [])


class TestIgnoreSetsNonEmpty(unittest.TestCase):
    # Guard against accidental emptying of the classification constants, which
    # would silently make every project look noise-free.
    def test_default_ignore_dirs(self):
        self.assertIn("node_modules", DEFAULT_IGNORE_DIRS)
        self.assertIn(".git", DEFAULT_IGNORE_DIRS)

    def test_generated_dirs(self):
        self.assertIn("exports", GENERATED_DIRS)
        self.assertIn("outputs", GENERATED_DIRS)


if __name__ == "__main__":
    unittest.main()
