# Output Contract

Defines what a finished decision-grade research engagement hands back. The deliverable is a
**decision report** — something a decision-maker can act on — not a topic survey or a
science-explainer essay. If the output reads like a Wikipedia article, the skill was used
wrong.

## Required sections

1. **Recommendation and the decision it answers.** Lead with the call and the specific
   decision it resolves, plus a confidence read tied to the strength mix in the ledger.
2. **Option comparison.** The candidate options from the hypothesis tree, with the case for
   and against each.
3. **Hypothesis tree status.** Which load-bearing hypotheses were resolved, which remain
   open, and which turned out not to be load-bearing.
4. **Track-D findings.** What the adversarial track attacked, what disconfirming evidence
   it found, and which hypotheses survived. A report with no Track-D section is not
   decision-grade.
5. **Conflict memo.** Any adjudicated source conflicts, with the resolution and reasoning;
   unresolved conflicts flagged as widened uncertainty.
6. **Evidence ledger.** Every conclusion-bearing claim with its source link and
   `observed / estimated / assumed` tag.
7. **Open risks and the trigger to revisit.** What would change the recommendation, and the
   cheap test worth running first if the call is close.
8. **Optional deck outline.** A slide skeleton for handing the decision up.

## Rules

- No conclusion that is not in the evidence ledger.
- Every number and claim tagged `observed`, `estimated`, or `assumed`.
- Local-first and reproducible: prefer captured local copies of sources to volatile links.
- When a load-bearing hypothesis rests mostly on `assumed` evidence, recommend a test
  before committing rather than projecting false confidence.
- Never include private consulting archives or client materials; published examples use a
  fictional decision and public or synthetic sources only.

## Local Run Artifacts

When scripts write files, use the ignored skill-local output folder:

```text
skills/decision-grade-research/output/
  YYYY-MM-DD-source-candidates.json
  YYYY-MM-DD-evidence-ledger.md
```

Use `--run-id` when multiple runs are needed on the same day, for example
`2026-06-04-evening`. Do not commit `output/` contents.
