# Example: synthetic workspace

A fully fabricated, worked example of the Project WIP Auditor. Every project name,
date, and path here is invented — nothing in this folder reflects a real local
workspace, real commit history, or any private path. It exists so a reader can see
the whole pipeline produce a real decision board without scanning their own disk.

## What the workspace represents

Six imaginary side projects sitting under one root, captured as signals in
[`scan.json`](scan.json). In a real run those signals come from
`scripts/scan_projects.py` walking the filesystem; here they are hand-written so the
result is stable and reviewable:

- `invoice-parser` — committed two days ago, 42 files, README + TODO (active, real work)
- `habit-tracker-app` — committed a week ago, 67 files, README (active, substantial)
- `newsletter-scraper` — last touched ~8 weeks ago, 23 files, README (stalled but real)
- `weekend-quiz-game` — touched ~6 weeks ago, only 3 files, no README (stalled, thin)
- `team-wiki-exporter` — quiet since last December, 88 files, README (abandoned but documented)
- `scratch-api-test` — untouched since September, 2 files, no git, no README (abandoned, throwaway)

## Reproduce the board

```bash
python3 scripts/build_wip_board.py \
    --input examples/synthetic-workspace/scan.json \
    --as-of 2026-06-04 \
    --json-out examples/synthetic-workspace/board.json \
    > examples/synthetic-workspace/board.md
```

`--as-of` is pinned so the output never drifts. The rendered board is checked in as
[`board.md`](board.md) and the structured version as [`board.json`](board.json).

## Why each project lands where it does

The board separates "active and worth finishing" from "dead weight you can drop":

- `invoice-parser` and `habit-tracker-app` are **active + substantial → ship**: keep momentum, drive to a finished cut.
- `newsletter-scraper` is **stalled + substantial → resume**: there is real work to pick back up, so it earns a scheduled block.
- `weekend-quiz-game` is **stalled + thin → kill**: three files and no README mean little is lost by dropping it.
- `team-wiki-exporter` is **abandoned + documented → archive**: too much work to delete outright, so keep it for the record.
- `scratch-api-test` is **abandoned + thin → kill**: a two-file scratch test, safe to delete.

This is the payoff of the skill: instead of a flat folder listing, you get a ranked
set of decisions — what to ship, what to resume, what to archive, and what to kill.
