# Decision-Grade Research

## What it does

Decision-Grade Research turns an uncertain choice into an auditable decision report.

It is built for decisions where the user needs to choose between options and explain the reasoning. The skill frames the decision as a hypothesis tree, runs parallel evidence tracks, adds an adversarial Track-D to falsify the leading answer, adjudicates source conflicts, and records claims in an evidence ledger.

The deliverable is not a topic explainer. It is a recommendation with traceable evidence and explicit uncertainty.

Live search is optional. The skill can work from user-provided sources only, or it can use the search adapter with `SEARCH_PROVIDER=tavily`, `SEARCH_PROVIDER=brave`, or `--provider none` for local source-candidate JSON.

## When to use it

- The user asks which option to choose and why.
- The decision has meaningful uncertainty or conflicting sources.
- The user needs a report that can be reviewed, challenged, or reused.
- The answer should distinguish observed facts, estimates, and assumptions.
- The agent needs a structured way to discover source candidates before building the evidence ledger.

Do not use it for quick factual lookups, beginner tutorials, generic deep research, or final licensed medical, legal, or financial advice.

## Example input

```text
We are deciding whether a fictional B2B analytics startup should enter the mid-market healthcare segment or stay focused on retail operations. Compare the two options and recommend a path for the next 12 months.
```

## Expected output

- Decision recommendation and option comparison
- Hypothesis tree showing what would change the decision
- Parallel research tracks and key findings
- Adversarial Track-D findings
- Conflict memo for contradictory evidence
- Evidence ledger with `observed` / `estimated` / `assumed` tags
- Open risks and triggers that would change the recommendation
- Optional deck outline
- Optional normalized source-candidate JSON from `scripts/search_sources.py`
- Date-named local output files under `skills/decision-grade-research/output/`, such as `2026-06-04-source-candidates.json` and `2026-06-04-evidence-ledger.md`

## Safety / boundaries

- Use public or user-provided sources only.
- Do not hard-code search API keys. Read them only from environment variables.
- Treat raw search results as candidates, not evidence.
- Do not publish private consulting archives, client data, account traces, or local absolute paths.
- Claims must trace to source URLs or file paths in the evidence ledger.
- When evidence conflicts, record the conflict and adjudication rather than hiding it.
- Public examples must be fictional or sanitized.
- `output/` contents are local run artifacts and should not be published.
