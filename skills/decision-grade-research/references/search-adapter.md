# Search Adapter

Decision-Grade Research can run from user-provided sources only, but live web research benefits from an optional search adapter. The adapter is intentionally vendor-light: the skill method depends on captured evidence, not on one search provider.

## Provider Policy

Supported provider modes:

- `none`: no network call; load source candidates from a local JSON file.
- `tavily`: use Tavily Search for agent-oriented web results.
- `brave`: use Brave Search for general web search results.

Use `none` when the user already supplied sources, when working offline, or when public examples must stay deterministic. Use `tavily` when the workflow needs agent-ready search results that can feed evidence extraction. Use `brave` when broad web discovery is enough and the agent will do extraction separately.

## Environment Variables

Never hard-code credentials in the skill, examples, or tests.

```bash
SEARCH_PROVIDER=tavily
TAVILY_API_KEY=...
BRAVE_API_KEY=...
```

If `--provider` is supplied to the script, it overrides `SEARCH_PROVIDER`. API keys are read only from environment variables.

## Query Planning

Do not search before the hypothesis tree exists. Queries should come from the decision structure:

- one query per high-impact hypothesis
- one query for each material conflict
- one adversarial query designed to disconfirm the leading recommendation
- one source-quality query for primary or official sources when available

Good queries name the decision variable, geography or segment, timeframe, and source type. Weak queries ask for the final answer directly.

## Source Candidate Contract

The adapter emits normalized JSON so later steps do not care which provider was used:

```json
{
  "query": "mid-market healthcare analytics HIPAA implementation timeline",
  "provider": "tavily",
  "results": [
    {
      "title": "Example title",
      "url": "https://example.com/source",
      "snippet": "Short provider snippet or summary.",
      "published_date": "2026-01-15",
      "score": 0.78
    }
  ]
}
```

These are candidates, not evidence yet. A result becomes evidence only after the agent reads or extracts the source, records the relevant claim, tags it `observed`, `estimated`, or `assumed`, and links it in the evidence ledger.

## Decision-Grade Rules

- Keep raw search output separate from the evidence ledger.
- Prefer primary sources, official documentation, regulator pages, filings, reports, and original data over secondary summaries.
- Capture enough metadata to re-find the source: URL, title, provider, query, retrieval date, and snippet.
- Run adversarial Track-D queries even if the first search results support the leading answer.
- When providers disagree, route the disagreement into `conflict-adjudication.md`.

## Public Examples

Public examples should use `--provider none` with synthetic `source_candidates.json`. Do not commit real API responses unless they are explicitly sanitized and licensed for reuse.

## Output Location

Write normalized source candidates into the ignored skill-local output folder:

```text
skills/decision-grade-research/output/
  YYYY-MM-DD-source-candidates.json
```

Use `--run-id` for repeat runs on the same day. Never commit live provider responses that contain private queries or account-specific context.
