# Project WIP Audit

_As of 2026-06-04; scanned roots: examples/synthetic-workspace/projects._

## Executive Recommendation

- Treat this as a decision board, not a freshness report: `6` projects scanned.
- Main focus should be capped at 2-3 workstreams. Current strongest focus candidates: **invoice-parser**.
- Close open loops before starting more work. Highest-priority close-loop items: **weekend-quiz-game**.
- Move park/archive/drop items out of daily attention unless they directly support the chosen focus.

## Action Counts

`focus: 1 · close_loop: 1 · resume: 1 · park: 1 · archive: 1 · drop: 1`

## 1. Focus Candidates

Choose at most a few. These are not all commitments; they are the short list for this week's main bets.

- **invoice-parser** — `hot` / `productized`, last real activity `2026-06-02`.
  - Recommendation: **make this a main workstream**.
  - Why: real work touched in the last 48h; choose whether this is one of the week's main bets.
  - Evidence: `src/parse_invoice.py`.

## 2. Close The Loop

These are the most dangerous attention leaks: recently touched, artifact-heavy, dirty, or under-documented.

- **weekend-quiz-game** — `parked` / `artifact-heavy`, last real activity `2026-05-10`.
  - Recommendation: **capture the stopping point or finish the artifact**.
  - Why: mostly generated/assets; preserve the output or write the decision note, then stop treating it as active.
  - Evidence: `notes/idea.txt`.
  - Noise check: newest file is exports/quiz-cards.png, but meaningful signal is notes/idea.txt.

## 3. Resume Only If It Matches The Current Goal

These are warm enough to restart, but should not compete with the main bets by default.

- **habit-tracker-app** — `active` / `productized`, last real activity `2026-05-28`.
  - Recommendation: **resume only if it matches the current goal**.
  - Why: warm enough to resume without heavy context rebuilding.
  - Evidence: `src/streaks.py`.

## 4. Park Or Archive

Keep these out of daily attention. Add a restart note only when the project has future value.

- **newsletter-scraper** — `cooling` / `productized`, last real activity `2026-05-20`.
  - Recommendation: **park deliberately**.
  - Why: real work, but not current; write a restart note before context fades.
  - Evidence: `scraper/feeds.py`.
- **team-wiki-exporter** — `cold` / `productized`, last real activity `2025-12-01`.
  - Recommendation: **archive for retrieval**.
  - Why: substantial historical work; archive for retrieval, not active attention.
  - Evidence: `exporter/export.py`.

## 5. Drop From Active Attention

These are thin or scratch-like. They may remain on disk, but should leave the mental WIP board.

- **scratch-api-test** — `cold` / `scratch`, last real activity `2025-09-03`.
  - Recommendation: **remove from active attention**.
  - Why: thin scratch folder; decide now or remove from the WIP surface.
  - Evidence: `scratch.py`.

