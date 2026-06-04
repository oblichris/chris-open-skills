# Triage Rubric

The output should answer: **what deserves attention, what needs closure, what can wait,
and what should leave the mental WIP board?**

## Actions

| Action | Meaning |
| --- | --- |
| `focus` | Candidate for this week's main work. Do not list more than a few without explaining tradeoffs. |
| `close_loop` | Recently touched but ambiguous, generated, or under-documented; capture the result, commit it, write a next action, or stop treating it as live. |
| `resume` | Warm and meaningful enough to pick back up if it matches the user's current goal. |
| `park` | Keep it, but remove from active attention. Add a restart note if it matters. |
| `archive` | Preserve for retrieval; do not spend current focus on it. |
| `drop` | Thin, scratchy, or stale enough to remove from active mental inventory. |

## Rules

- `hot` + `productized/substantial` -> `focus`
- `hot` + `artifact-heavy/thin/documented` -> `close_loop`
- `active` + dirty git repo -> `close_loop`
- `active` + meaningful documented work -> `resume`
- `active` + low substance -> `park`
- `cooling` + substantial work -> `park`
- `cooling` + low substance -> `archive`
- `parked/cold` + substantial documented work -> `archive`
- `parked/cold` + scratch/thin work -> `drop`

## Reading The Board

The board is intentionally opinionated. It should not say "everything is active." If many
projects were touched recently, the board must still separate:

- current focus candidates
- recent loose ends that need closure
- warm projects that are only worth resuming if they match the user's weekly goal
- parked/archive material
- scratch folders that should leave the user's attention

The auditor never deletes or moves files. It only recommends.
