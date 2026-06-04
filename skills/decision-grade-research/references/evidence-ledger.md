# Evidence Ledger

The evidence ledger is the audit backbone of the report: every claim that informs the
recommendation is recorded with the source it traces to and the strength of that source. Its
rule is simple and strict — **no claim appears in the conclusion that is not in the ledger.**
That is what makes the research "decision-grade": a reader can follow any conclusion back to
its evidence and judge it.

## What a ledger entry holds

- `id` — a stable claim identifier (C1, C2, …).
- `hypothesis` — which hypothesis from the tree this claim speaks to.
- `statement` — the claim itself, stated precisely.
- `strength` — `observed` (directly evidenced), `estimated` (derived/modelled), or
  `assumed` (believed without direct evidence).
- `sources` — one or more references, each with a URL or local file path, title, and date.

## Strength tagging

Tag honestly. `observed` requires a real source; `estimated` requires the basis to be
shown; `assumed` is allowed but is a flag, not a free pass — a recommendation resting on
`assumed` load-bearing claims is fragile and the report must say so. The mix of strengths
across load-bearing claims is itself a finding: mostly `observed` is a confident call,
mostly `assumed` means "decide whether to test before committing."

## Validation (what `build_evidence_ledger.py` checks)

The script renders the ledger to Markdown and validates it, reporting warnings such as:

- a claim tagged `observed` or `estimated` with **no source** attached;
- a claim referencing a **hypothesis id that does not exist** in the tree;
- a **load-bearing hypothesis with no supporting claim** in the ledger.

Warnings are surfaced, not silently fixed — they tell the researcher where the evidence is
thin before the report is finalized. The ledger feeds both the conflict memo (which claims
are disputed) and the final report (which claims justify the recommendation).
