# Output Contract

Defines what a finished WIP audit hands back. The deliverable is a **decision board**, not
a file listing: the reader should be able to act on it in one pass.

## Two artifacts

`build_wip_board.py` can emit a human-readable Markdown board on stdout and, with
`--json-out`, a structured JSON board for downstream tooling. In normal skill use, write
both files into the ignored skill-local output folder:

```text
skills/project-wip-auditor/output/
  YYYY-MM-DD-scan.json
  YYYY-MM-DD-wip-audit.json
  YYYY-MM-DD-wip-audit.md
```

The JSON is the audit source; the Markdown is the readable hand-back. Both are derived from
the same evaluation so they never disagree.

Use `--run-id` when multiple audits are needed on the same day, for example
`2026-06-04-evening`.

## Markdown board

The board must contain, in order:

1. **Title and context line** — `As of <date>` and the scanned roots, so the board is
   self-dating and reproducible.
2. **Executive recommendation** — 3-5 bullets that tell the user what to focus on,
   what to close, what to stop thinking about, and why.
3. **Summary line** — total project count and the count in each action
   (`focus / close_loop / resume / park / archive / drop`).
4. **Focus candidates** — no more than a few items unless tradeoffs are explained.
5. **Close-loop items** — recently touched projects that need capture, commit, final output,
   or parking.
6. **Resume/park/archive/drop tables** with one row per project.

## JSON board

A `{ "as_of", "roots", "board": [...] }` object. Each board entry carries `name`, `path`,
`state`, `shape`, `last_real_activity`, `days_since`, `action`, `rationale`,
`meaningful_signal`, `noise_note`, `is_git`, and file-count signals.

## Rules

- Every project appears exactly once and carries exactly one action.
- Every action carries a short rationale tied to the project's state and substance.
- The final answer must include insights from Markdown reading for major recommendations.
- Do not present a metadata-only scan as a WIP audit.
- The board recommends; it never moves or deletes files. Acting on `kill`/`archive` is left
  to the user.
- Published examples must use a synthetic workspace — never real folder names, real paths,
  or real commit history.
