# Scan Contract

Defines what the auditor reads, what it treats as a "project", and the guarantee that
the scan never changes anything on disk.

## Inputs

- One or more **root directories** (`--root`, repeatable). Each immediate sub-directory
  of a root is treated as one candidate project. Roots are not recursed into beyond that
  first level for the project boundary; signal collection then walks each project fully.
- Optional extra **ignore names** (`--ignore`, repeatable) merged with the default ignore
  set: `.git`, `node_modules`, `__pycache__`, `.venv`, `venv`, `.idea`, `.vscode`, `dist`,
  `build`, `.next`, `.cache`, `.pytest_cache`. Hidden directories (names starting with `.`)
  are skipped as projects.

## Signals collected per project

- `last_commit` — date of the most recent git commit (`git log -1 --format=%cI`), or null
  when the project is not a git repository.
- `newest_mtime` — the most recent file modification time anywhere under the project.
- `meaningful_mtime` — the newest Markdown/code/config/data file outside generated or output folders.
- `noise_mtime` — newest generated asset, export, image, media, or report-like artifact.
- `has_readme` / `has_todo` — whether a README, AGENTS, CLAUDE, Agent, or TODO marker file is present.
- `file_count`, `meaningful_file_count`, `noisy_file_count`, and `size_bytes`.
- `is_git` — whether a `.git` directory exists.

## Required content reading

The scanner is only the first pass. A real WIP audit must then read selected Markdown files:

- Entry docs: `README.md`, `AGENTS.md`, `Agent.md`, `CLAUDE.md`.
- Planning docs: `roadmap.md`, `outputplan.md`, `INDEX.md`, `*计划*.md`.
- Recent Markdown files in the last meaningful edit window.

For each decision-worthy project, extract:

- project purpose
- current status or implemented surface
- open loop / next development priority
- whether the project is a product, content operation, learning workspace, research archive, or one-off artifact pipeline

If the final answer does not mention insights from project Markdown, the audit is incomplete.

## Hard guarantees

- **Read-only.** The scan opens and `stat()`s files; it never writes, moves, renames, or
  deletes anything in the scanned tree. The only writes are to the explicit `--output` path.
- **Private by default.** The mechanical scan output avoids source contents. The human
  audit may summarize local Markdown for the user, but public examples must remain synthetic.
- **Deterministic shape.** Projects are emitted sorted by name so two scans of an unchanged
  tree produce identical structure, which keeps downstream boards reviewable in diffs.

The output is a JSON document (`scanned_at`, `roots`, `projects[]`) consumed verbatim by
`build_wip_board.py`.
