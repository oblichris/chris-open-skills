from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "skills" / "all2md" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from convert_all import (  # noqa: E402
    SourceItem,
    classify,
    default_run_name,
    output_path_for,
    safe_prefix,
    slugify,
)


class TestClassify(unittest.TestCase):
    def test_pdf(self):
        self.assertEqual(classify(Path("report.pdf")), "pdf")

    def test_doc_variants(self):
        for ext in (".docx", ".pptx", ".xlsx", ".html", ".htm"):
            with self.subTest(ext=ext):
                self.assertEqual(classify(Path(f"file{ext}")), "doc")

    def test_image_variants(self):
        for ext in (".png", ".jpg", ".jpeg"):
            with self.subTest(ext=ext):
                self.assertEqual(classify(Path(f"photo{ext}")), "image")

    def test_audio_variants(self):
        for ext in (".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"):
            with self.subTest(ext=ext):
                self.assertEqual(classify(Path(f"clip{ext}")), "audio")

    def test_video_variants(self):
        for ext in (".mp4", ".mov", ".mkv", ".webm", ".avi"):
            with self.subTest(ext=ext):
                self.assertEqual(classify(Path(f"movie{ext}")), "video")

    def test_unsupported_is_skip(self):
        for ext in (".txt", ".json", ".csv", ".md", ""):
            with self.subTest(ext=ext):
                self.assertEqual(classify(Path(f"notes{ext}")), "skip")

    def test_case_insensitive(self):
        self.assertEqual(classify(Path("REPORT.PDF")), "pdf")
        self.assertEqual(classify(Path("Deck.PPTX")), "doc")
        self.assertEqual(classify(Path("Scan.JPEG")), "image")


class TestSlugify(unittest.TestCase):
    def test_plain_alnum(self):
        self.assertEqual(slugify("quarterly-report"), "quarterly-report")

    def test_spaces_become_dashes(self):
        self.assertEqual(slugify("Q1 revenue data"), "Q1-revenue-data")

    def test_multiple_separators_collapsed(self):
        self.assertEqual(slugify("a   b/c.d"), "a-b-c-d")

    def test_leading_trailing_stripped(self):
        self.assertEqual(slugify("---hello---"), "hello")

    def test_dots_slashes_become_dashes(self):
        self.assertEqual(slugify("path/to/file.name"), "path-to-file-name")

    def test_disallowed_chars_dropped(self):
        self.assertEqual(slugify("a@b#c$d"), "abcd")

    def test_empty_returns_sources(self):
        self.assertEqual(slugify(""), "sources")

    def test_only_symbols_returns_sources(self):
        self.assertEqual(slugify("@#$%"), "sources")

    def test_underscore_preserved(self):
        self.assertEqual(slugify("my_file"), "my_file")

    def test_truncated_to_80(self):
        long = "a" * 200
        self.assertEqual(len(slugify(long)), 80)


class TestSafePrefix(unittest.TestCase):
    def test_first_use_returns_base(self):
        used: set[str] = set()
        self.assertEqual(safe_prefix(Path("/tmp/interviews"), used), Path("interviews"))
        self.assertIn("interviews", used)

    def test_collision_appends_index(self):
        used: set[str] = {"reports"}
        self.assertEqual(safe_prefix(Path("/data/reports"), used), Path("reports-2"))
        self.assertEqual(safe_prefix(Path("/data/reports"), used), Path("reports-3"))

    def test_falls_back_to_input_when_no_name(self):
        used: set[str] = set()
        self.assertEqual(safe_prefix(Path("/"), used), Path("input"))


class TestOutputPathFor(unittest.TestCase):
    def test_builds_md_path_under_prefix(self):
        item = SourceItem(
            path=Path("/src/pkg/report.pdf"),
            root=Path("/src/pkg"),
            output_prefix=Path("pkg"),
        )
        out = output_path_for(item, Path("/out"))
        self.assertEqual(out, Path("/out/pkg/report.md"))

    def test_root_level_file_has_no_prefix(self):
        item = SourceItem(
            path=Path("/src/notes.docx"),
            root=Path("/src"),
            output_prefix=Path(),
        )
        out = output_path_for(item, Path("/out"))
        self.assertEqual(out, Path("/out/notes.md"))

    def test_preserves_nested_relative_structure(self):
        item = SourceItem(
            path=Path("/src/pkg/sub/deep/audio.mp3"),
            root=Path("/src/pkg"),
            output_prefix=Path("pkg"),
        )
        out = output_path_for(item, Path("/out"))
        self.assertEqual(out, Path("/out/pkg/sub/deep/audio.md"))


class TestDefaultRunName(unittest.TestCase):
    def test_single_input_uses_stem(self):
        name = default_run_name([Path("/data/financials.xlsx")], None)
        self.assertIn("financials", name)

    def test_multiple_inputs_uses_multi_source(self):
        name = default_run_name([Path("/data/a.pdf"), Path("/data/b.docx")], None)
        self.assertIn("multi-source", name)

    def test_requested_overrides_source(self):
        name = default_run_name([Path("/data/a.pdf")], "custom-run")
        self.assertTrue(name.endswith("-custom-run"))

    def test_always_has_timestamp_prefix(self):
        import re

        name = default_run_name([Path("/data/a.pdf")], None)
        self.assertRegex(name, r"^\d{8}-\d{6}-")


if __name__ == "__main__":
    unittest.main()
