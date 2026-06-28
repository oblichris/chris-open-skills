from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "skills" / "decision-grade-research" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from build_evidence_ledger import (  # noqa: E402
    main,
    render_markdown,
    validate,
)


def _research(
    *,
    hypotheses=None,
    claims=None,
    decision="Should we do X?",
):
    return {
        "decision": decision,
        "hypotheses": hypotheses if hypotheses is not None else [],
        "claims": claims if claims is not None else [],
    }


def _hyp(hid="H1", impact="high", status="open", statement="Some hypothesis"):
    return {"id": hid, "impact": impact, "status": status, "statement": statement}


def _claim(
    cid="C1",
    hypothesis="H1",
    strength="observed",
    statement="Some claim",
    sources=None,
):
    return {
        "id": cid,
        "hypothesis": hypothesis,
        "strength": strength,
        "statement": statement,
        "sources": sources if sources is not None else [],
    }


def _source(ref="https://example.org/paper", title="Paper", date="2026-01"):
    return {"ref": ref, "title": title, "date": date}


class TestValidateClean(unittest.TestCase):
    def test_no_warnings_when_all_rules_satisfied(self):
        data = _research(
            hypotheses=[_hyp(hid="H1", impact="high")],
            claims=[_claim(hypothesis="H1", strength="observed", sources=[_source()])],
        )
        self.assertEqual(validate(data), [])

    def test_empty_data_no_warnings(self):
        self.assertEqual(validate({}), [])

    def test_assumed_claim_without_source_is_ok(self):
        data = _research(
            hypotheses=[_hyp(hid="H1", impact="high")],
            claims=[_claim(hypothesis="H1", strength="assumed", sources=[])],
        )
        self.assertEqual(validate(data), [])


class TestValidateSourcedClaims(unittest.TestCase):
    def test_observed_without_source_warns(self):
        data = _research(
            hypotheses=[_hyp(hid="H1")],
            claims=[_claim(cid="C1", hypothesis="H1", strength="observed", sources=[])],
        )
        warnings = validate(data)
        self.assertEqual(len(warnings), 1)
        self.assertIn("C1", warnings[0])
        self.assertIn("observed", warnings[0])

    def test_estimated_without_source_warns(self):
        data = _research(
            hypotheses=[_hyp(hid="H1")],
            claims=[_claim(cid="C2", hypothesis="H1", strength="estimated", sources=[])],
        )
        warnings = validate(data)
        self.assertEqual(len(warnings), 1)
        self.assertIn("C2", warnings[0])
        self.assertIn("estimated", warnings[0])

    def test_observed_with_source_no_warn(self):
        data = _research(
            hypotheses=[_hyp(hid="H1")],
            claims=[_claim(hypothesis="H1", strength="observed", sources=[_source()])],
        )
        warnings = validate(data)
        sourced_warnings = [w for w in warnings if "no source" in w]
        self.assertEqual(sourced_warnings, [])


class TestValidateUnknownHypothesis(unittest.TestCase):
    def test_unknown_hypothesis_reference_warns(self):
        data = _research(
            hypotheses=[_hyp(hid="H1")],
            claims=[_claim(cid="C1", hypothesis="HZZ", strength="assumed")],
        )
        warnings = validate(data)
        unknown = [w for w in warnings if "unknown hypothesis" in w]
        self.assertEqual(len(unknown), 1)
        self.assertIn("C1", unknown[0])
        self.assertIn("HZZ", unknown[0])

    def test_valid_hypothesis_reference_no_warn(self):
        data = _research(
            hypotheses=[_hyp(hid="H1")],
            claims=[_claim(hypothesis="H1", strength="assumed")],
        )
        warnings = validate(data)
        unknown = [w for w in warnings if "unknown hypothesis" in w]
        self.assertEqual(unknown, [])


class TestValidateLoadBearingHypothesis(unittest.TestCase):
    def test_high_impact_hypothesis_without_claim_warns(self):
        data = _research(
            hypotheses=[_hyp(hid="H1", impact="high")],
            claims=[],
        )
        warnings = validate(data)
        load_bearing = [w for w in warnings if "load-bearing" in w]
        self.assertEqual(len(load_bearing), 1)
        self.assertIn("H1", load_bearing[0])

    def test_medium_impact_hypothesis_without_claim_no_warn(self):
        data = _research(
            hypotheses=[_hyp(hid="H1", impact="medium")],
            claims=[],
        )
        warnings = validate(data)
        load_bearing = [w for w in warnings if "load-bearing" in w]
        self.assertEqual(load_bearing, [])

    def test_low_impact_hypothesis_without_claim_no_warn(self):
        data = _research(
            hypotheses=[_hyp(hid="H1", impact="low")],
            claims=[],
        )
        warnings = validate(data)
        load_bearing = [w for w in warnings if "load-bearing" in w]
        self.assertEqual(load_bearing, [])

    def test_high_impact_with_claim_no_warn(self):
        data = _research(
            hypotheses=[_hyp(hid="H1", impact="high")],
            claims=[_claim(hypothesis="H1", strength="observed", sources=[_source()])],
        )
        warnings = validate(data)
        load_bearing = [w for w in warnings if "load-bearing" in w]
        self.assertEqual(load_bearing, [])


class TestValidateMultipleWarnings(unittest.TestCase):
    def test_multiple_warning_types_in_single_pass(self):
        data = _research(
            hypotheses=[
                _hyp(hid="H1", impact="high"),
                _hyp(hid="H2", impact="high"),
            ],
            claims=[
                _claim(cid="C1", hypothesis="H1", strength="observed", sources=[]),
                _claim(cid="C2", hypothesis="HZZ", strength="assumed"),
            ],
        )
        warnings = validate(data)
        self.assertEqual(len(warnings), 3)
        warning_text = "\n".join(warnings)
        self.assertIn("no source", warning_text)
        self.assertIn("unknown hypothesis", warning_text)
        self.assertIn("load-bearing", warning_text)


class TestRenderMarkdown(unittest.TestCase):
    def test_contains_decision(self):
        md = render_markdown(_research(decision="Should we ship?"), [])
        self.assertIn("Should we ship?", md)

    def test_contains_evidence_ledger_header(self):
        md = render_markdown(_research(), [])
        self.assertIn("# Evidence Ledger", md)

    def test_contains_hypothesis_id(self):
        data = _research(hypotheses=[_hyp(hid="H1", statement="Growth is real")])
        md = render_markdown(data, [])
        self.assertIn("H1", md)
        self.assertIn("Growth is real", md)

    def test_contains_claim_with_source(self):
        data = _research(
            hypotheses=[_hyp(hid="H1")],
            claims=[_claim(
                cid="C1",
                hypothesis="H1",
                statement="Revenue grew 20%",
                sources=[_source(ref="https://example.org/report", title="Annual Report")],
            )],
        )
        md = render_markdown(data, [])
        self.assertIn("Revenue grew 20%", md)
        self.assertIn("Annual Report", md)
        self.assertIn("https://example.org/report", md)

    def test_claim_with_no_sources_shows_dash(self):
        data = _research(
            hypotheses=[_hyp(hid="H1")],
            claims=[_claim(cid="C1", hypothesis="H1", strength="assumed", sources=[])],
        )
        md = render_markdown(data, [])
        self.assertIn("\u2014", md)

    def test_strength_mix_section(self):
        data = _research(
            hypotheses=[_hyp(hid="H1")],
            claims=[
                _claim(cid="C1", hypothesis="H1", strength="observed", sources=[_source()]),
                _claim(cid="C2", hypothesis="H1", strength="assumed"),
            ],
        )
        md = render_markdown(data, [])
        self.assertIn("## Strength mix", md)
        self.assertIn("observed: 1", md)
        self.assertIn("assumed: 1", md)

    def test_no_warnings_message(self):
        md = render_markdown(_research(), [])
        self.assertIn("No integrity warnings", md)

    def test_warning_lines_rendered(self):
        warnings = ["C1: tagged 'observed' but has no source attached"]
        md = render_markdown(_research(), warnings)
        self.assertIn("WARNING", md)
        self.assertIn("no source attached", md)


class TestMainCli(unittest.TestCase):
    def test_stdin_clean_data_exit_zero(self):
        import io
        from contextlib import redirect_stdout
        data = _research(
            hypotheses=[_hyp(hid="H1", impact="high")],
            claims=[_claim(hypothesis="H1", strength="observed", sources=[_source()])],
        )
        old_stdin = sys.stdin
        sys.stdin = io.StringIO(json.dumps(data))
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                rc = main([])
        finally:
            sys.stdin = old_stdin
        self.assertEqual(rc, 0)
        self.assertIn("# Evidence Ledger", buf.getvalue())

    def test_stdin_warnings_normal_mode_exit_zero(self):
        import io
        from contextlib import redirect_stderr, redirect_stdout
        data = _research(
            hypotheses=[_hyp(hid="H1", impact="high")],
            claims=[_claim(cid="C1", hypothesis="H1", strength="observed", sources=[])],
        )
        old_stdin = sys.stdin
        sys.stdin = io.StringIO(json.dumps(data))
        err = io.StringIO()
        buf = io.StringIO()
        try:
            with redirect_stderr(err), redirect_stdout(buf):
                rc = main([])
        finally:
            sys.stdin = old_stdin
        self.assertEqual(rc, 0)
        self.assertIn("warning:", err.getvalue())

    def test_stdin_warnings_strict_mode_exit_nonzero(self):
        import io
        from contextlib import redirect_stderr, redirect_stdout
        data = _research(
            hypotheses=[_hyp(hid="H1", impact="high")],
            claims=[_claim(cid="C1", hypothesis="H1", strength="observed", sources=[])],
        )
        old_stdin = sys.stdin
        sys.stdin = io.StringIO(json.dumps(data))
        err = io.StringIO()
        buf = io.StringIO()
        try:
            with redirect_stderr(err), redirect_stdout(buf):
                rc = main(["--strict"])
        finally:
            sys.stdin = old_stdin
        self.assertEqual(rc, 1)

    def test_strict_mode_clean_data_exit_zero(self):
        import io
        from contextlib import redirect_stdout
        data = _research(
            hypotheses=[_hyp(hid="H1", impact="high")],
            claims=[_claim(hypothesis="H1", strength="observed", sources=[_source()])],
        )
        old_stdin = sys.stdin
        sys.stdin = io.StringIO(json.dumps(data))
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                rc = main(["--strict"])
        finally:
            sys.stdin = old_stdin
        self.assertEqual(rc, 0)

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

    def test_missing_input_file_exit_two(self):
        import io
        from contextlib import redirect_stderr
        err = io.StringIO()
        with redirect_stderr(err):
            rc = main(["--input", "/nonexistent/path/research.json"])
        self.assertEqual(rc, 2)
        self.assertIn("does not exist", err.getvalue())

    def test_invalid_json_exit_two(self):
        import io
        from contextlib import redirect_stderr
        old_stdin = sys.stdin
        sys.stdin = io.StringIO("{not valid json")
        err = io.StringIO()
        try:
            with redirect_stderr(err):
                rc = main([])
        finally:
            sys.stdin = old_stdin
        self.assertEqual(rc, 2)
        self.assertIn("invalid JSON", err.getvalue())

    def test_output_dir_writes_file(self):
        import io
        import tempfile
        from contextlib import redirect_stdout
        data = _research(
            hypotheses=[_hyp(hid="H1", impact="high")],
            claims=[_claim(hypothesis="H1", strength="observed", sources=[_source()])],
        )
        old_stdin = sys.stdin
        sys.stdin = io.StringIO(json.dumps(data))
        buf = io.StringIO()
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                with redirect_stdout(buf):
                    rc = main(["--output-dir", tmpdir, "--run-id", "2026-06-15"])
            finally:
                sys.stdin = old_stdin
            self.assertEqual(rc, 0)
            outfile = Path(tmpdir) / "2026-06-15-evidence-ledger.md"
            self.assertTrue(outfile.exists())
            content = outfile.read_text(encoding="utf-8")
            self.assertIn("# Evidence Ledger", content)


class TestExampleFixture(unittest.TestCase):
    """Validate the shipped example JSON against the validator."""

    ROOT = Path(__file__).resolve().parents[1]

    def test_example_fixture_has_expected_warnings(self):
        fixture = self.ROOT / "skills" / "decision-grade-research" / "examples" / "fictional-market-entry-decision" / "research.json"
        data = json.loads(fixture.read_text(encoding="utf-8"))
        warnings = validate(data)
        load_bearing = [w for w in warnings if "load-bearing" in w]
        self.assertEqual(load_bearing, [], "all high-impact hypotheses should have claims")

    def test_example_fixture_renders(self):
        fixture = self.ROOT / "skills" / "decision-grade-research" / "examples" / "fictional-market-entry-decision" / "research.json"
        data = json.loads(fixture.read_text(encoding="utf-8"))
        warnings = validate(data)
        md = render_markdown(data, warnings)
        self.assertIn("# Evidence Ledger", md)
        self.assertIn("Meridian", md)


if __name__ == "__main__":
    unittest.main()
