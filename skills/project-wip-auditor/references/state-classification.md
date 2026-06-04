# State Classification

The classifier is a decision surface, not a freshness report. A project should not be called
"active" just because an image, export, cache file, or generated report changed recently.
The scanner records both `newest_mtime` and `meaningful_mtime`; the board uses the latter
plus git commits when deciding whether the project deserves attention.

## Real activity date

Use the most recent of:

- `last_commit`: strongest signal of intentional work
- `meaningful_mtime`: newest Markdown, code, config, data, or text file outside generated/output folders

Keep `newest_mtime` only as a noise diagnostic. If it differs from the real activity date,
report that the apparent freshness may come from generated assets.

## States

| State | Real activity age | Meaning |
| --- | --- | --- |
| `hot` | 0-2 days | Currently in the user's hands; must either become a priority or be closed cleanly. |
| `active` | 3-7 days | Warm enough to resume without heavy context rebuilding. |
| `cooling` | 8-21 days | Context is fading; needs a restart note or deliberate parking. |
| `parked` | 22-90 days | Outside the current work loop; keep only as backlog or archive. |
| `cold` | 90+ days | Historical material, not active WIP. |
| `unclear` | no usable signal | Needs manual inspection before any recommendation is trusted. |

## Project shape

State alone is not enough. Classify the project shape:

- `productized`: README/agent guide plus at least 20 meaningful files
- `substantial`: at least 20 meaningful files but weaker documentation
- `documented`: has README/agent guide but smaller body
- `artifact-heavy`: mostly images, exports, generated reports, or assets
- `scratch`: three or fewer meaningful files and no README/agent guide
- `thin`: small project without enough evidence to treat as a real workstream

The final action combines state and shape. A hot artifact-heavy folder is not "ship"; it is
"close the loop". A cooling substantial project is not "resume everything"; it is "park with
a restart note unless it matches this week's goal."
