# Project WIP Auditor

## What it does

Project WIP Auditor reconstructs what has actually been happening across a local project workspace.

It scans one or more project roots, collects read-only signals such as git history, meaningful file modification times, noisy/generated file modification times, README/TODO presence, and project shape, then classifies each project as `hot`, `active`, `cooling`, `parked`, `cold`, or `unclear`. The final output is a conclusion-first WIP decision board with a recommended action: `focus`, `close_loop`, `resume`, `park`, `archive`, or `drop`.

This is work archaeology, not calendar planning.

Web search is not a core dependency. The point of this skill is the local environment: filesystem signals, git history, and project artifacts.

## When to use it

- The user has many local project folders and wants to regain control.
- The user asks what they have been working on recently.
- The user wants to decide what to focus, close, resume, park, archive, or drop.
- The agent is allowed to read local folders and git metadata.
- The agent is allowed to read project Markdown files enough to understand purpose, status, open loops, and next action.

Do not use it for single-repo code review, daily scheduling, or tasks that do not involve scanning real directories.

## Example input

```text
Scan these two synthetic roots:

- examples/synthetic-workspace
- another sanitized project archive

Write the Markdown WIP board and JSON summary into the skill's ignored output folder.
```

## Expected output

- Executive recommendation before any tables or raw status.
- Per-project state: `hot`, `active`, `cooling`, `parked`, `cold`, or `unclear`
- Last real activity evidence from git commits or meaningful file mtimes
- README/TODO, project-shape, and noise signals
- Recommended action: `focus`, `close_loop`, `resume`, `park`, `archive`, or `drop`
- One-line rationale per project
- Board-level summary with focus candidates, close-loop items, and items to remove from active attention
- Date-named local output files under `skills/project-wip-auditor/output/`, such as `2026-06-04-scan.json`, `2026-06-04-wip-audit.json`, and `2026-06-04-wip-audit.md`

## Safety / boundaries

- Read-only by default. Do not move, delete, rename, or edit project files.
- Treat real project names, paths, commit messages, and work history as private unless the user explicitly says otherwise.
- Public examples must use synthetic folder names and fabricated signals.
- Large generated outputs, caches, local absolute paths, private logs, and `output/` contents should not be published.
