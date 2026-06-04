# Example: fictional market-entry decision

A worked example of the evidence-ledger stage on a fully invented decision. "Meridian
Analytics" is not a real company; every hypothesis, claim, number, and source here is
fabricated. The `https://example.org/internal-fixture/...` references stand in for
user-provided source captures; they demonstrate the evidence pattern without using
real paths.

## The decision under research

Should Meridian, a fictional B2B analytics company, **enter the mid-market healthcare
segment in the next 12 months, or stay focused on retail?** The structured research lives
in [`research.json`](research.json): the decision, a five-node hypothesis tree, and the
claims that inform it.

The optional search-adapter stage is represented by [`source_candidates.json`](source_candidates.json).
It uses `provider: none`, so the example stays deterministic and never calls a live API.

## What the ledger shows

The hypothesis tree separates the load-bearing questions (high-impact) from the rest:

- **H1 — segment is large enough** (resolved): supported by an estimated $420M TAM (C1) and
  observed 11% YoY spend growth (C2).
- **H2 — reachable through the existing motion** (resolved): 14% of recent inbound demos
  came from healthcare unprompted (C3, observed).
- **H3 — product can meet HIPAA compliance in 12 months** (open): rests on claim C4, which
  is tagged **`assumed` with no source** — the single most fragile link in the case.
- **H4 — economics beat retail** (resolved, medium impact): longer CAC payback but 1.8x ACV (C5).
- **H5 — brand transfers** (open, low impact): not load-bearing, logged but not chased.

The strength mix (2 observed, 2 estimated, 1 assumed) makes the risk legible at a glance:
the entry case is mostly evidenced, but the one `assumed` claim sits on a high-impact open
hypothesis. That is exactly the kind of thing Track-D would attack and the final report
would flag — "the HIPAA-feasibility assumption is doing the load; run a two-week
architecture spike before committing."

## Reproduce the ledger

```bash
python3 scripts/build_evidence_ledger.py \
    --input examples/fictional-market-entry-decision/research.json \
    --output examples/fictional-market-entry-decision/ledger.md
```

The rendered ledger is checked in as [`ledger.md`](ledger.md): the hypothesis table, the
claims table with linked sources and strength tags, the strength-mix summary, and the
validation section. Pass `--strict` to make any integrity warning fail a CI gate.

To normalize source candidates without network calls:

```bash
python3 scripts/search_sources.py \
    --provider none \
    --input examples/fictional-market-entry-decision/source_candidates.json \
    --output-dir skills/decision-grade-research/output \
    --run-id 2026-06-04
```
