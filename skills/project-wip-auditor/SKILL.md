---
name: project-wip-auditor
description: Reconstruct what you have actually been working on by scanning local project folders, then output a work-in-progress decision board. Use when the user has many project directories and wants to know which are active, stalled, dormant, or abandoned, and what to resume, ship, kill, or archive. The skill reads the real filesystem — git history, file mtimes, READMEs, TODOs. Do not use for calendar or schedule management, single-repo code review, or any task that does not involve scanning local project directories.
---

# Project WIP Auditor

## Use This Skill For

- walk one or more project roots and reconstruct what the user has actually been working on
- read project entry Markdown (`README.md`, `AGENTS.md`, `CLAUDE.md`, roadmap/plan notes) and recent Markdown files before making recommendations
- classify each project as `hot`, `active`, `cooling`, `parked`, `cold`, or `unclear` from real signals
- triage each project into `focus`, `close_loop`, `resume`, `park`, `archive`, or `drop` with a short rationale
- produce a WIP decision board with explicit insight, suggested work focus, and next actions

This is work archaeology / WIP audit, not calendar time management. It is agent-native: a chat assistant cannot do this because it must read the real filesystem and git history.
Web search is not part of the core workflow; use it only if a scanned project explicitly points to a public URL that the user wants checked.

## Do Not Route Here

- calendar, schedule, or daily time-blocking requests
- single-repo code review or architecture analysis
- anything that does not involve scanning local project directories

## Default Workflow

1. Use `references/scan-contract.md` to confirm the root directories to scan and any ignore rules.
2. Run `scripts/scan_projects.py` to enumerate projects and collect signals: last git commit, meaningful file mtimes, noisy generated-file mtimes, README/TODO presence, and project shape.
3. Read the entry docs and recent Markdown for the top focus/close-loop/resume candidates. Extract project purpose, current state, open loop, and likely next useful action.
4. Use `references/state-classification.md` to classify each project as `hot` / `active` / `cooling` / `parked` / `cold` / `unclear`.
5. Use `references/triage-rubric.md` to assign each project a next action: `focus` / `close_loop` / `resume` / `park` / `archive` / `drop`.
6. Run `scripts/build_wip_board.py` to assemble the mechanical board, then add a human insight layer from the Markdown reading.
7. Use `references/output-contract.md` to emit the WIP decision board (Markdown + JSON) plus a short work recommendation.

## Core Rules

- read-only by default: never modify, move, or delete the user's project files
- classify from observed signals, but separate meaningful edits from generated artifacts and cache noise
- do not stop at metadata; read enough Markdown to understand what the project is for and why it matters
- every project gets exactly one recommended next action plus a one-line rationale
- surface the few projects that matter and explain what the user should actually do next
- never publish the user's real folder names, paths, or commit messages; public examples use a synthetic workspace only

## Output Contract

- deliver a WIP decision board, not a raw file listing
- include a top-level recommendation: what to focus on this week, what to close, and what to stop thinking about
- per project, include:
  - name and root path (redacted in any published example)
  - state: `hot` / `active` / `cooling` / `parked` / `cold` / `unclear`
  - last real activity signal (last commit date or meaningful file mtime)
  - recommended action: `focus` / `close_loop` / `resume` / `park` / `archive` / `drop`
  - one-line rationale
- board-level summary: counts per state, the top resume candidates, and the clear kill list
