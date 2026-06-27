from __future__ import annotations

import io
import json
import re
import sys
import tempfile
import unittest
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "agent-chart"
sys.path.insert(0, str(SKILL_ROOT))

from agent_chart.cli import main  # noqa: E402

REVENUE_CSV = SKILL_ROOT / "examples" / "revenue.csv"
SPEC_JSON = SKILL_ROOT / "examples" / "specs" / "revenue_bar.spec.json"
RUN_FOLDER_RE = re.compile(r"^\d{8}_\d{6}$")


class _CliRunner:
    """Run cli.main() while capturing stdout/stderr, optionally into a temp output dir."""

    def __init__(self) -> None:
        self.stdout = ""
        self.stderr = ""
        self.rc: int | None = None
        self.base: Path | None = None

    def run(self, argv: list[str]) -> int:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = main(argv)
        self.stdout = out.getvalue()
        self.stderr = err.getvalue()
        self.rc = rc
        return rc

    @contextmanager
    def run_into_tmp(self, argv: list[str]):
        with tempfile.TemporaryDirectory() as tmp:
            self.base = Path(tmp)
            rc = self.run(list(argv) + ["--output-dir", tmp])
            yield rc


class TestCliInspect(unittest.TestCase):
    def test_inspect_prints_fields_and_returns_zero(self):
        runner = _CliRunner()
        rc = runner.run(["--input", str(REVENUE_CSV), "--inspect"])
        self.assertEqual(rc, 0)
        self.assertIn("字段列表", runner.stdout)
        self.assertIn("收入", runner.stdout)
        self.assertIn("利润率", runner.stdout)


class TestCliRenderFromPrompt(unittest.TestCase):
    def test_bar_writes_svg_png_spec_into_timestamped_folder(self):
        runner = _CliRunner()
        with runner.run_into_tmp([
            "--input", str(REVENUE_CSV),
            "--prompt", "生成柱状图，x=年份，y=收入，标题=公司收入增长趋势",
            "--output", "revenue_bar",
            "--format", "svg,png",
        ]) as rc:
            self.assertEqual(rc, 0, runner.stderr)
            subdirs = [p for p in runner.base.iterdir() if p.is_dir()]
            self.assertEqual(len(subdirs), 1, "exactly one timestamped run folder expected")
            run_dir = subdirs[0]
            self.assertRegex(run_dir.name, RUN_FOLDER_RE, "run folder must be YYYYMMDD_HHMMSS")
            self.assertTrue((run_dir / "revenue_bar.svg").exists())
            self.assertTrue((run_dir / "revenue_bar.png").exists())
            self.assertTrue((run_dir / "revenue_bar.spec.json").exists())

    def test_render_reports_generated_files_and_summary(self):
        runner = _CliRunner()
        with runner.run_into_tmp([
            "--input", str(REVENUE_CSV),
            "--prompt", "生成柱状图，x=年份，y=收入",
            "--output", "revenue_bar",
            "--format", "svg",
        ]) as rc:
            self.assertEqual(rc, 0)
            self.assertIn("数据校验通过", runner.stdout)
            self.assertIn("revenue_bar", runner.stdout)


class TestCliRenderFromPastedData(unittest.TestCase):
    def test_pasted_data_writes_into_timestamped_folder(self):
        runner = _CliRunner()
        with runner.run_into_tmp([
            "--data", "年份,收入\n2021,100\n2022,130",
            "--prompt", "生成柱状图，x=年份，y=收入，标题=粘贴趋势",
            "--output", "pasted_bar",
            "--format", "svg",
        ]) as rc:
            self.assertEqual(rc, 0, runner.stderr)
            subdirs = [p for p in runner.base.iterdir() if p.is_dir()]
            self.assertEqual(len(subdirs), 1)
            run_dir = subdirs[0]
            self.assertTrue((run_dir / "pasted_bar.svg").exists())
            self.assertTrue((run_dir / "pasted_bar.spec.json").exists())


class TestCliRenderFromSpec(unittest.TestCase):
    def test_spec_file_renders_without_prompt(self):
        runner = _CliRunner()
        with runner.run_into_tmp([
            "--input", str(REVENUE_CSV),
            "--spec", str(SPEC_JSON),
            "--output", "from_spec",
            "--format", "svg",
        ]) as rc:
            self.assertEqual(rc, 0, runner.stderr)
            subdirs = [p for p in runner.base.iterdir() if p.is_dir()]
            self.assertEqual(len(subdirs), 1)
            run_dir = subdirs[0]
            self.assertTrue((run_dir / "from_spec.svg").exists())
            spec_path = run_dir / "from_spec.spec.json"
            self.assertTrue(spec_path.exists())
            saved = json.loads(spec_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["chart_type"], "bar")
            self.assertEqual(saved["x"], "年份")
            self.assertEqual(saved["y"], "收入")


class TestCliValidationFailures(unittest.TestCase):
    def test_missing_field_returns_one_and_writes_no_image(self):
        runner = _CliRunner()
        with runner.run_into_tmp([
            "--input", str(REVENUE_CSV),
            "--prompt", "生成柱状图，x=年份，y=不存在字段，标题=错误测试",
            "--output", "should_fail",
            "--format", "svg",
        ]) as rc:
            self.assertEqual(rc, 1)
            self.assertIn("错误", runner.stderr)
            images = list(runner.base.rglob("*.svg")) + list(runner.base.rglob("*.png"))
            self.assertEqual(images, [], "no chart image should be generated on validation failure")

    def test_ambiguous_prompt_returns_one_and_writes_no_image(self):
        runner = _CliRunner()
        with runner.run_into_tmp([
            "--input", str(REVENUE_CSV),
            "--prompt", "生成柱状图，展示趋势",
            "--output", "should_fail_ambiguous",
            "--format", "svg",
        ]) as rc:
            self.assertEqual(rc, 1)
            self.assertIn("错误", runner.stderr)
            images = list(runner.base.rglob("*.svg")) + list(runner.base.rglob("*.png"))
            self.assertEqual(images, [], "no chart image should be generated when fields are missing")

    def test_unsupported_format_returns_one(self):
        runner = _CliRunner()
        with runner.run_into_tmp([
            "--input", str(REVENUE_CSV),
            "--prompt", "生成柱状图，x=年份，y=收入",
            "--output", "bad_format",
            "--format", "pdf",
        ]) as rc:
            self.assertEqual(rc, 1)
            self.assertIn("pdf", runner.stderr.lower())


class TestCliMissingInput(unittest.TestCase):
    def test_missing_input_file_returns_one(self):
        runner = _CliRunner()
        rc = runner.run([
            "--input", "/nonexistent/revenue.csv",
            "--prompt", "生成柱状图，x=年份，y=收入",
            "--output", "x",
            "--format", "svg",
        ])
        self.assertEqual(rc, 1)
        self.assertIn("does not exist", runner.stderr.lower())


if __name__ == "__main__":
    unittest.main()
