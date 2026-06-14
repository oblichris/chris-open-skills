from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "skills" / "project-wip-auditor" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from build_wip_board import (  # noqa: E402
    action_label,
    classify,
    days_since,
    evaluate,
    last_real_activity,
    shape,
    triage,
)


AS_OF = __import__("datetime").date(2026, 6, 14)


class TestDaysSince(unittest.TestCase):
    def test_none_returns_none(self):
        self.assertIsNone(days_since(None, AS_OF))

    def test_same_day(self):
        self.assertEqual(days_since("2026-06-14", AS_OF), 0)

    def test_one_day(self):
        self.assertEqual(days_since("2026-06-13", AS_OF), 1)

    def test_many_days(self):
        self.assertEqual(days_since("2026-03-15", AS_OF), 91)


class TestLastRealActivity(unittest.TestCase):
    def test_prefers_commit_over_meaningful(self):
        project = {"last_commit": "2026-06-10", "meaningful_mtime": "2026-06-01"}
        self.assertEqual(last_real_activity(project), "2026-06-10")

    def test_prefers_meaningful_when_newer(self):
        project = {"last_commit": "2026-06-01", "meaningful_mtime": "2026-06-12"}
        self.assertEqual(last_real_activity(project), "2026-06-12")

    def test_falls_back_to_newest_mtime(self):
        project = {"last_commit": None, "meaningful_mtime": None, "newest_mtime": "2026-06-05"}
        self.assertEqual(last_real_activity(project), "2026-06-05")

    def test_all_missing_returns_none(self):
        self.assertIsNone(last_real_activity({}))


class TestShape(unittest.TestCase):
    def test_scratch(self):
        result = shape({"meaningful_file_count": 2, "file_count": 5, "has_readme": False, "noisy_file_count": 0})
        self.assertEqual(result, "scratch")

    def test_artifact_heavy(self):
        result = shape({"meaningful_file_count": 5, "file_count": 10, "has_readme": False, "noisy_file_count": 8})
        self.assertEqual(result, "artifact-heavy")

    def test_productized(self):
        result = shape({"meaningful_file_count": 25, "file_count": 30, "has_readme": True, "noisy_file_count": 3})
        self.assertEqual(result, "productized")

    def test_substantial_without_readme(self):
        result = shape({"meaningful_file_count": 25, "file_count": 30, "has_readme": False, "noisy_file_count": 3})
        self.assertEqual(result, "substantial")

    def test_documented(self):
        result = shape({"meaningful_file_count": 10, "file_count": 20, "has_readme": True, "noisy_file_count": 2})
        self.assertEqual(result, "documented")

    def test_thin(self):
        result = shape({"meaningful_file_count": 10, "file_count": 20, "has_readme": False, "noisy_file_count": 2})
        self.assertEqual(result, "thin")


class TestClassify(unittest.TestCase):
    def test_none_is_unclear(self):
        self.assertEqual(classify(None, "thin"), "unclear")

    def test_hot_boundary(self):
        self.assertEqual(classify(0, "thin"), "hot")
        self.assertEqual(classify(2, "thin"), "hot")

    def test_active_boundary(self):
        self.assertEqual(classify(3, "thin"), "active")
        self.assertEqual(classify(7, "thin"), "active")

    def test_cooling_boundary(self):
        self.assertEqual(classify(8, "thin"), "cooling")
        self.assertEqual(classify(21, "thin"), "cooling")

    def test_parked_boundary(self):
        self.assertEqual(classify(22, "thin"), "parked")
        self.assertEqual(classify(90, "thin"), "parked")

    def test_cold(self):
        self.assertEqual(classify(91, "thin"), "cold")


class TestTriage(unittest.TestCase):
    def _project(self, **overrides):
        project = {"has_readme": False, "dirty": None, "name": "demo"}
        project.update(overrides)
        return project

    def test_scratch_drops(self):
        action, _ = triage("hot", "scratch", self._project())
        self.assertEqual(action, "drop")

    def test_artifact_heavy_close_loop(self):
        action, _ = triage("hot", "artifact-heavy", self._project())
        self.assertEqual(action, "close_loop")

    def test_hot_productized_focus(self):
        action, _ = triage("hot", "productized", self._project(has_readme=True))
        self.assertEqual(action, "focus")

    def test_hot_thin_close_loop(self):
        action, _ = triage("hot", "thin", self._project())
        self.assertEqual(action, "close_loop")

    def test_active_dirty_close_loop(self):
        action, _ = triage("active", "documented", self._project(has_readme=True, dirty=True))
        self.assertEqual(action, "close_loop")

    def test_active_productized_resume(self):
        action, _ = triage("active", "productized", self._project(has_readme=True))
        self.assertEqual(action, "resume")

    def test_active_thin_park(self):
        action, _ = triage("active", "thin", self._project())
        self.assertEqual(action, "park")

    def test_cooling_substantial_park(self):
        action, _ = triage("cooling", "substantial", self._project())
        self.assertEqual(action, "park")

    def test_cooling_thin_archive(self):
        action, _ = triage("cooling", "thin", self._project())
        self.assertEqual(action, "archive")

    def test_parked_with_readme_archive(self):
        action, _ = triage("parked", "documented", self._project(has_readme=True))
        self.assertEqual(action, "archive")

    def test_parked_no_readme_drop(self):
        action, _ = triage("parked", "thin", self._project(has_readme=False))
        self.assertEqual(action, "drop")

    def test_cold_substantial_archive(self):
        action, _ = triage("cold", "substantial", self._project())
        self.assertEqual(action, "archive")

    def test_cold_thin_drop(self):
        action, _ = triage("cold", "thin", self._project())
        self.assertEqual(action, "drop")

    def test_unclear_park(self):
        action, _ = triage("unclear", "thin", self._project())
        self.assertEqual(action, "park")

    def test_rationale_is_nonempty(self):
        for state in ["hot", "active", "cooling", "parked", "cold", "unclear"]:
            for proj_shape in ["scratch", "artifact-heavy", "productized", "substantial", "documented", "thin"]:
                _, rationale = triage(state, proj_shape, self._project())
                self.assertTrue(rationale, f"empty rationale for {state}/{proj_shape}")


class TestActionLabel(unittest.TestCase):
    def test_focus(self):
        self.assertEqual(action_label("focus"), "make this a main workstream")

    def test_close_loop(self):
        self.assertEqual(action_label("close_loop"), "capture the stopping point or finish the artifact")

    def test_unknown_passthrough(self):
        self.assertEqual(action_label("bogus"), "bogus")


class TestEvaluateIntegration(unittest.TestCase):
    def test_hot_productized_project(self):
        project = {
            "name": "core-app",
            "path": "/dev/core-app",
            "meaningful_file_count": 30,
            "file_count": 40,
            "noisy_file_count": 5,
            "has_readme": True,
            "dirty": False,
            "is_git": True,
            "last_commit": "2026-06-13",
            "meaningful_mtime": "2026-06-12",
            "newest_mtime": "2026-06-13",
            "meaningful_mtime_path": "src/main.py",
            "newest_mtime_path": "dist/build.js",
            "last_commit_subject": "feat: add module",
        }
        result = evaluate(project, AS_OF)
        self.assertEqual(result["state"], "hot")
        self.assertEqual(result["shape"], "productized")
        self.assertEqual(result["action"], "focus")

    def test_cold_thin_project_drops(self):
        project = {
            "name": "old-scratch",
            "path": "/dev/old-scratch",
            "meaningful_file_count": 5,
            "file_count": 12,
            "noisy_file_count": 2,
            "has_readme": False,
            "dirty": None,
            "is_git": False,
            "last_commit": None,
            "meaningful_mtime": "2025-12-01",
            "newest_mtime": "2025-12-01",
            "meaningful_mtime_path": "notes.txt",
            "newest_mtime_path": "notes.txt",
            "last_commit_subject": None,
        }
        result = evaluate(project, AS_OF)
        self.assertEqual(result["state"], "cold")
        self.assertEqual(result["shape"], "thin")
        self.assertEqual(result["action"], "drop")

    def test_noise_note_emitted_when_meaningful_differs(self):
        project = {
            "name": "assets-heavy",
            "path": "/dev/assets-heavy",
            "meaningful_file_count": 6,
            "file_count": 20,
            "noisy_file_count": 16,
            "has_readme": False,
            "dirty": None,
            "is_git": False,
            "last_commit": None,
            "meaningful_mtime": "2026-06-01",
            "newest_mtime": "2026-06-12",
            "meaningful_mtime_path": "README.md",
            "newest_mtime_path": "exports/big.png",
            "last_commit_subject": None,
        }
        result = evaluate(project, AS_OF)
        self.assertTrue(result["noise_note"])

    def test_no_noise_note_when_paths_match(self):
        project = {
            "name": "simple",
            "path": "/dev/simple",
            "meaningful_file_count": 3,
            "file_count": 5,
            "noisy_file_count": 0,
            "has_readme": False,
            "dirty": None,
            "is_git": False,
            "last_commit": None,
            "meaningful_mtime": "2026-06-10",
            "newest_mtime": "2026-06-10",
            "meaningful_mtime_path": "main.py",
            "newest_mtime_path": "main.py",
            "last_commit_subject": None,
        }
        result = evaluate(project, AS_OF)
        self.assertFalse(result["noise_note"])


if __name__ == "__main__":
    unittest.main()
