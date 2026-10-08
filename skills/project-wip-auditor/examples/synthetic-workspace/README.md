# Example: synthetic workspace

A fully fabricated, worked example of the Project WIP Auditor. Every project name,
date, and path here is invented — nothing in this folder reflects a real local
workspace, real commit history, or any private path. It exists so a reader can see
the whole pipeline produce a real decision board without scanning their own disk.

## What the workspace represents

Six imaginary side projects sitting under one root, captured as signals in
[`scan.json`](scan.json). In a real run those signals come from
`scripts/scan_projects.py` walking the filesystem; here they are hand-written so the
result is stable and reviewable. The fixture uses the current scan contract:
`meaningful_file_count`, `meaningful_mtime`, and `noisy_file_count`, not raw file
counts or the newest mtime alone.

- `invoice-parser` — real code committed on 2026-06-02, 42 meaningful files, README (hot, productized)
- `weekend-quiz-game` — 36 of 40 files are exports; the newest file is a PNG from 2026-06-03, but the last meaningful note is 2026-05-10 (artifact-heavy)
- `habit-tracker-app` — committed on 2026-05-28, 60 meaningful files, README, clean git tree (active, productized)
- `newsletter-scraper` — last real work on 2026-05-20, 23 meaningful files, README (cooling, productized)
- `team-wiki-exporter` — last meaningful edit on 2025-12-01, 80 meaningful files, README (cold, productized)
- `scratch-api-test` — two files, no README, no git, untouched since 2025-09-03 (scratch)

## Reproduce the board

From `skills/project-wip-auditor/`:

```bash
python3 scripts/build_wip_board.py \
    --input examples/synthetic-workspace/scan.json \
    --as-of 2026-06-04 \
    --json-out examples/synthetic-workspace/board.json \
    > examples/synthetic-workspace/board.md
```

`--as-of` is pinned so the output never drifts. The rendered board is checked in as
[`board.md`](board.md) and the structured version as [`board.json`](board.json).
Re-running the command above should reproduce those files exactly.

## Why each project lands where it does

The board separates current bets from loose ends and from work that should leave
daily attention:

- `invoice-parser` is **hot + productized → focus**: real work in the last 48 hours, so it is a candidate for this week's main bet.
- `weekend-quiz-game` is **artifact-heavy → close_loop**: a fresh export makes the folder look current, but almost everything in it is generated. Preserve the output or write the decision note, then stop treating it as active.
- `habit-tracker-app` is **active + productized → resume**: warm enough to pick back up, but only if it matches the current goal.
- `newsletter-scraper` is **cooling + productized → park**: real work, but not current; write a restart note before the context fades.
- `team-wiki-exporter` is **cold + productized → archive**: substantial historical work, kept for retrieval rather than active attention.
- `scratch-api-test` is **scratch → drop**: two files and no README; it can stay on disk, but it should leave the mental WIP board.

This is the payoff of the skill: instead of a flat folder listing, you get one
next action per project — what to focus, what to close, what to resume, what to
park, what to archive, and what to drop.
