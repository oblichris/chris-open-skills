from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "skills" / "decision-grade-research" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from search_sources import (  # noqa: E402
    normalize_existing,
    normalize_result,
)


class TestNormalizeResult(unittest.TestCase):
    def test_all_fields_set(self):
        result = normalize_result(
            title="Annual Report",
            url="https://example.org/report",
            snippet="Revenue grew 20%.",
            published_date="2026-01",
            score=0.9,
        )
        self.assertEqual(result["title"], "Annual Report")
        self.assertEqual(result["url"], "https://example.org/report")
        self.assertEqual(result["snippet"], "Revenue grew 20%.")
        self.assertEqual(result["published_date"], "2026-01")
        self.assertEqual(result["score"], 0.9)

    def test_none_values_become_empty_strings(self):
        result = normalize_result(title=None, url=None, snippet=None, published_date=None)
        self.assertEqual(result["title"], "")
        self.assertEqual(result["url"], "")
        self.assertEqual(result["snippet"], "")
        self.assertEqual(result["published_date"], "")

    def test_score_none_preserved(self):
        result = normalize_result()
        self.assertIsNone(result["score"])

    def test_no_arguments(self):
        result = normalize_result()
        self.assertEqual(result["title"], "")
        self.assertEqual(result["url"], "")
        self.assertEqual(result["snippet"], "")
        self.assertEqual(result["published_date"], "")
        self.assertIsNone(result["score"])

    def test_returns_all_contract_keys(self):
        result = normalize_result()
        expected_keys = {"title", "url", "snippet", "published_date", "score"}
        self.assertEqual(set(result.keys()), expected_keys)


class TestNormalizeExistingDictPayload(unittest.TestCase):
    def test_dict_payload_preserves_query(self):
        payload = {"query": "market size", "results": []}
        out = normalize_existing(payload, "none")
        self.assertEqual(out["query"], "market size")

    def test_dict_payload_uses_provider_argument(self):
        payload = {"query": "x", "results": []}
        out = normalize_existing(payload, "none")
        self.assertEqual(out["provider"], "none")

    def test_dict_payload_provider_overridden_by_payload(self):
        payload = {"query": "x", "provider": "tavily", "results": []}
        out = normalize_existing(payload, "none")
        self.assertEqual(out["provider"], "tavily")

    def test_dict_payload_without_provider_keeps_argument(self):
        payload = {"query": "x", "results": []}
        out = normalize_existing(payload, "brave")
        self.assertEqual(out["provider"], "brave")

    def test_empty_results_list(self):
        out = normalize_existing({"query": "x", "results": []}, "none")
        self.assertEqual(out["results"], [])

    def test_retrieved_at_is_iso_date(self):
        import re

        out = normalize_existing({"query": "x", "results": []}, "none")
        self.assertRegex(out["retrieved_at"], r"^\d{4}-\d{2}-\d{2}$")


class TestNormalizeExistingListPayload(unittest.TestCase):
    def test_list_payload_has_empty_query(self):
        out = normalize_existing([], "none")
        self.assertEqual(out["query"], "")

    def test_list_payload_results_preserved(self):
        out = normalize_existing(
            [{"title": "A", "url": "https://example.org/a"}],
            "none",
        )
        self.assertEqual(len(out["results"]), 1)
        self.assertEqual(out["results"][0]["title"], "A")


class TestNormalizeExistingFieldAliases(unittest.TestCase):
    def test_url_alias_href(self):
        out = normalize_existing(
            [{"title": "A", "href": "https://example.org/a"}],
            "none",
        )
        self.assertEqual(out["results"][0]["url"], "https://example.org/a")

    def test_url_preferred_over_href(self):
        out = normalize_existing(
            [{"title": "A", "url": "https://preferred.org", "href": "https://discarded.org"}],
            "none",
        )
        self.assertEqual(out["results"][0]["url"], "https://preferred.org")

    def test_snippet_alias_content(self):
        out = normalize_existing(
            [{"title": "A", "url": "u", "content": "body text"}],
            "none",
        )
        self.assertEqual(out["results"][0]["snippet"], "body text")

    def test_snippet_alias_description(self):
        out = normalize_existing(
            [{"title": "A", "url": "u", "description": "a summary"}],
            "none",
        )
        self.assertEqual(out["results"][0]["snippet"], "a summary")

    def test_snippet_precedence_snippet_first(self):
        out = normalize_existing(
            [{"title": "A", "url": "u", "snippet": "primary", "content": "secondary", "description": "tertiary"}],
            "none",
        )
        self.assertEqual(out["results"][0]["snippet"], "primary")

    def test_published_date_alias_date(self):
        out = normalize_existing(
            [{"title": "A", "url": "u", "date": "2026-03-01"}],
            "none",
        )
        self.assertEqual(out["results"][0]["published_date"], "2026-03-01")

    def test_result_without_any_fields(self):
        out = normalize_existing([{}], "none")
        self.assertEqual(out["results"][0]["title"], "")
        self.assertEqual(out["results"][0]["url"], "")
        self.assertEqual(out["results"][0]["snippet"], "")
        self.assertEqual(out["results"][0]["published_date"], "")
        self.assertIsNone(out["results"][0]["score"])


class TestNormalizeExistingOutputKeys(unittest.TestCase):
    def test_output_has_required_top_level_keys(self):
        out = normalize_existing({"query": "x", "results": []}, "none")
        for key in ("query", "provider", "retrieved_at", "results"):
            self.assertIn(key, out)

    def test_each_result_has_contract_keys(self):
        out = normalize_existing(
            [{"title": "A", "url": "u"}],
            "none",
        )
        result = out["results"][0]
        for key in ("title", "url", "snippet", "published_date", "score"):
            self.assertIn(key, result)


class TestExampleFixture(unittest.TestCase):
    """Validate the shipped example source_candidates fixture normalizes cleanly."""

    ROOT = Path(__file__).resolve().parents[1]

    def test_fixture_normalizes_to_two_results(self):
        fixture = self.ROOT / "skills" / "decision-grade-research" / "examples" / "fictional-market-entry-decision" / "source_candidates.json"
        data = json.loads(fixture.read_text(encoding="utf-8"))
        out = normalize_existing(data, "none")
        self.assertEqual(len(out["results"]), 2)
        self.assertEqual(out["query"], data["query"])

    def test_fixture_preserves_provider(self):
        fixture = self.ROOT / "skills" / "decision-grade-research" / "examples" / "fictional-market-entry-decision" / "source_candidates.json"
        data = json.loads(fixture.read_text(encoding="utf-8"))
        out = normalize_existing(data, "none")
        self.assertEqual(out["provider"], "none")

    def test_fixture_results_have_urls_and_scores(self):
        fixture = self.ROOT / "skills" / "decision-grade-research" / "examples" / "fictional-market-entry-decision" / "source_candidates.json"
        data = json.loads(fixture.read_text(encoding="utf-8"))
        out = normalize_existing(data, "none")
        for result in out["results"]:
            self.assertTrue(result["url"])
            self.assertIsNotNone(result["score"])


if __name__ == "__main__":
    unittest.main()
