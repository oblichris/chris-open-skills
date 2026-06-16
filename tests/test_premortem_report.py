from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "skills" / "premortem-redteam" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from generate_html_report import (  # noqa: E402
    band,
    main,
    render,
)


def _plan(title="Notewise launch", summary="A fictional launch.", decision="Commit runway.", horizon="12 months"):
    return {"title": title, "summary": summary, "decision": decision, "horizon": horizon}


def _fm(
    fid="F1",
    title="Channel under-delivers",
    story="The channel collapsed.",
    breaks_assumption="A1",
    likelihood=4,
    impact=5,
    indicator="Weekly trial signups",
    threshold="Below 50% for 3 weeks",
    response="Open a second channel",
    mitigation="Pre-build a content buffer",
    owner="Founder / growth",
):
    return {
        "id": fid,
        "title": title,
        "story": story,
        "breaks_assumption": breaks_assumption,
        "likelihood": likelihood,
        "impact": impact,
        "indicator": indicator,
        "threshold": threshold,
        "response": response,
        "mitigation": mitigation,
        "owner": owner,
    }


def _analysis(plan=None, assumptions=None, failure_modes=None, residual_risk="Accepted knowingly."):
    return {
        "plan": plan if plan is not None else _plan(),
        "assumptions": assumptions if assumptions is not None else [],
        "failure_modes": failure_modes if failure_modes is not None else [],
        "residual_risk": residual_risk,
    }


class TestBand(unittest.TestCase):
    def test_high_boundary(self):
        self.assertEqual(band(15), "hi")

    def test_just_below_high_is_mid(self):
        self.assertEqual(band(14), "mid")

    def test_mid_boundary(self):
        self.assertEqual(band(8), "mid")

    def test_just_below_mid_is_lo(self):
        self.assertEqual(band(7), "lo")

    def test_zero_is_lo(self):
        self.assertEqual(band(0), "lo")

    def test_max_priority_is_hi(self):
        self.assertEqual(band(25), "hi")


class TestRenderPlan(unittest.TestCase):
    def test_contains_plan_title(self):
        html_out = render(_analysis(plan=_plan(title="Acme Pivot")))
        self.assertIn("Acme Pivot", html_out)

    def test_contains_plan_summary(self):
        html_out = render(_analysis(plan=_plan(summary="A fictional 3-person launch.")))
        self.assertIn("A fictional 3-person launch.", html_out)

    def test_contains_decision(self):
        html_out = render(_analysis(plan=_plan(decision="Commit a 6-month runway.")))
        self.assertIn("Commit a 6-month runway.", html_out)

    def test_contains_horizon(self):
        html_out = render(_analysis(plan=_plan(horizon="12 months post-launch")))
        self.assertIn("12 months post-launch", html_out)

    def test_plan_title_defaults_when_missing(self):
        html_out = render({"plan": {}, "failure_modes": []})
        self.assertIn("Pre-mortem Red Team", html_out)


class TestRenderAssumptions(unittest.TestCase):
    def test_load_bearing_assumption_tagged(self):
        data = _analysis(
            assumptions=[{"id": "A1", "statement": "Content drives signups.", "load_bearing": True}],
        )
        html_out = render(data)
        self.assertIn("A1", html_out)
        self.assertIn("load-bearing", html_out)

    def test_non_load_bearing_assumption_not_tagged(self):
        data = _analysis(
            assumptions=[{"id": "A4", "statement": "Incumbents stay still.", "load_bearing": False}],
        )
        html_out = render(data)
        self.assertIn("A4", html_out)
        self.assertNotIn("load-bearing", html_out)


class TestRenderFailureModes(unittest.TestCase):
    def test_priority_computed_and_shown(self):
        data = _analysis(failure_modes=[_fm(likelihood=4, impact=5)])
        html_out = render(data)
        self.assertIn("20", html_out)

    def test_failure_mode_title_and_story_rendered(self):
        data = _analysis(failure_modes=[_fm(title="Channel collapses", story="Reach fell 70%.")])
        html_out = render(data)
        self.assertIn("Channel collapses", html_out)
        self.assertIn("Reach fell 70%.", html_out)

    def test_breaks_assumption_rendered(self):
        data = _analysis(failure_modes=[_fm(breaks_assumption="A2")])
        html_out = render(data)
        self.assertIn("A2", html_out)

    def test_monitoring_fields_rendered(self):
        data = _analysis(
            failure_modes=[
                _fm(indicator="Trial signups", threshold="<50%", response="Open channel", mitigation="Buffer", owner="Growth"),
            ],
        )
        html_out = render(data)
        self.assertIn("Trial signups", html_out)
        self.assertIn("&lt;50%", html_out)
        self.assertIn("Open channel", html_out)
        self.assertIn("Buffer", html_out)
        self.assertIn("Growth", html_out)

    def test_ranked_descending_by_priority(self):
        data = _analysis(
            failure_modes=[
                _fm(fid="low", title="LOW-MODE", likelihood=1, impact=2),
                _fm(fid="high", title="HIGH-MODE", likelihood=5, impact=5),
                _fm(fid="mid", title="MID-MODE", likelihood=3, impact=3),
            ],
        )
        html_out = render(data)
        high_pos = html_out.find("HIGH-MODE")
        mid_pos = html_out.find("MID-MODE")
        low_pos = html_out.find("LOW-MODE")
        self.assertLess(high_pos, mid_pos, "highest priority should render before mid")
        self.assertLess(mid_pos, low_pos, "mid priority should render before low")

    def test_empty_failure_modes_does_not_crash(self):
        html_out = render(_analysis(failure_modes=[]))
        self.assertIn("Ranked failure modes", html_out)


class TestRenderResidualRisk(unittest.TestCase):
    def test_residual_risk_shown(self):
        data = _analysis(residual_risk="Single founder is a fragile dependency.")
        html_out = render(data)
        self.assertIn("Single founder is a fragile dependency.", html_out)
        self.assertIn("Residual risk", html_out)

    def test_no_residual_risk_omits_section(self):
        data = _analysis()
        data.pop("residual_risk")
        html_out = render(data)
        self.assertNotIn("Residual risk", html_out)


class TestRenderEscaping(unittest.TestCase):
    def test_html_special_characters_escaped(self):
        data = _analysis(
            plan=_plan(title="<script>alert(1)</script>"),
            failure_modes=[_fm(title="<b>bold</b> & <i>italic</i>")],
        )
        html_out = render(data)
        self.assertNotIn("<script>alert(1)</script>", html_out)
        self.assertIn("&lt;script&gt;", html_out)
        self.assertIn("&lt;b&gt;", html_out)
        self.assertIn("&amp;", html_out)


class TestMainCli(unittest.TestCase):
    def test_stdin_clean_data_exit_zero(self):
        import io
        from contextlib import redirect_stdout

        data = _analysis(failure_modes=[_fm()])
        old_stdin = sys.stdin
        sys.stdin = io.StringIO(json.dumps(data))
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                rc = main([])
        finally:
            sys.stdin = old_stdin
        self.assertEqual(rc, 0)
        self.assertIn("Pre-mortem Red Team", buf.getvalue())

    def test_empty_input_exit_two(self):
        import io
        from contextlib import redirect_stderr

        old_stdin = sys.stdin
        sys.stdin = io.StringIO("")
        err = io.StringIO()
        try:
            with redirect_stderr(err):
                rc = main([])
        finally:
            sys.stdin = old_stdin
        self.assertEqual(rc, 2)

    def test_output_dir_writes_file(self):
        import io
        import tempfile
        from contextlib import redirect_stdout

        data = _analysis(failure_modes=[_fm()])
        old_stdin = sys.stdin
        sys.stdin = io.StringIO(json.dumps(data))
        buf = io.StringIO()
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                with redirect_stdout(buf):
                    rc = main(["--output-dir", tmpdir, "--run-id", "2026-06-16"])
            finally:
                sys.stdin = old_stdin
            self.assertEqual(rc, 0)
            outfile = Path(tmpdir) / "2026-06-16-premortem-report.html"
            self.assertTrue(outfile.exists())
            content = outfile.read_text(encoding="utf-8")
            self.assertIn("Pre-mortem Red Team", content)

    def test_input_file_flag(self):
        import io
        import tempfile
        from contextlib import redirect_stdout

        data = _analysis(failure_modes=[_fm()])
        buf = io.StringIO()
        with tempfile.TemporaryDirectory() as tmpdir:
            infile = Path(tmpdir) / "analysis.json"
            infile.write_text(json.dumps(data), encoding="utf-8")
            with redirect_stdout(buf):
                rc = main(["--input", str(infile)])
        self.assertEqual(rc, 0)
        self.assertIn("Pre-mortem Red Team", buf.getvalue())


class TestExampleFixture(unittest.TestCase):
    """Validate the shipped example JSON renders into a complete report."""

    ROOT = Path(__file__).resolve().parents[1]

    def test_example_fixture_renders(self):
        fixture = self.ROOT / "skills" / "premortem-redteam" / "examples" / "fictional-launch-premortem" / "analysis.json"
        data = json.loads(fixture.read_text(encoding="utf-8"))
        html_out = render(data)
        self.assertIn("Notewise launch", html_out)
        self.assertIn("Ranked failure modes", html_out)
        self.assertIn("Monitoring", html_out)
        self.assertIn("Residual risk", html_out)

    def test_example_fixture_failure_modes_ranked_descending(self):
        fixture = self.ROOT / "skills" / "premortem-redteam" / "examples" / "fictional-launch-premortem" / "analysis.json"
        data = json.loads(fixture.read_text(encoding="utf-8"))
        html_out = render(data)
        priorities = [(20, "LinkedIn channel under-delivers"),
                      (15, "Trials do not convert to paid"),
                      (12, "v1 slips past Q3"),
                      (6, "Incumbent ships comparable AI")]
        positions = [html_out.find(title) for _, title in priorities]
        for earlier, later in zip(positions, positions[1:]):
            self.assertLess(earlier, later, "higher-priority failure mode must appear before lower-priority one")


if __name__ == "__main__":
    unittest.main()
