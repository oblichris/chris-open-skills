# Chris Open Skills

Reusable agent skills for decision research, local project auditing, and plan stress-testing.

This repository is meant to be used directly: each skill has an agent-facing `SKILL.md`, supporting references, optional scripts, examples, and a human guide. The point is not to publish a prompt pile; the point is to provide reusable workflows with clear inputs, outputs, boundaries, and validation.

The first batch focuses on two things:

- method-driven skills, where the framework is the product
- agent-native skills, where the workflow uses filesystem, scripts, git history, or local evidence that a plain chat assistant cannot inspect

## Skill Catalog

| Skill | What It Does | Status | Guide |
| --- | --- | --- | --- |
| Decision-Grade Research | Turns a real decision under uncertainty into a source-backed decision report with hypothesis trees, parallel evidence tracks, adversarial Track-D, conflict adjudication, and an evidence ledger. | staged | [Guide](docs/skills/decision-grade-research.md) |
| Project WIP Auditor | Scans local project roots to reconstruct active, stalled, dormant, and abandoned work, then produces a WIP decision board with resume / ship / kill / archive recommendations. | staged | [Guide](docs/skills/project-wip-auditor.md) |
| Pre-mortem Red Team | Stress-tests a plan by assuming it failed, attacking load-bearing assumptions, ranking failure modes, and defining monitoring thresholds and mitigations. | staged | [Guide](docs/skills/premortem-redteam.md) |
| all2md | Converts mixed source-material packages into AI-ready Markdown, preserving folder structure and writing index plus manifest artifacts for traceable review. | staged | [Guide](docs/skills/all2md.md) |

The structured source of truth is [registry/skills.json](registry/skills.json).

## How To Use These Skills

Each skill has two entry points:

- For agents: read `skills/<slug>/SKILL.md`, then follow the referenced files in `references/`.
- For humans: read `docs/skills/<slug>.md` for when to use it, what input to provide, what output to expect, and what safety boundaries apply.

The helper scripts are optional deterministic utilities. They are not meant to replace the skill method; they make specific steps reproducible.

Live web discovery is optional. `decision-grade-research` includes a search adapter that can use Tavily, Brave, or local source-candidate JSON:

```bash
SEARCH_PROVIDER=tavily
TAVILY_API_KEY=...
BRAVE_API_KEY=...
```

Do not commit API keys or raw private search output. Public examples use local JSON fixtures.

Run the repository tests before publishing or after changing any skill:

```bash
python3 -m unittest discover -s tests -v
```

## Repository Layout

```text
chris-open-skills/
├── README.md
├── LICENSE
├── docs/
│   └── skills/
├── registry/
│   └── skills.json
└── skills/
    └── <skill-slug>/
        ├── SKILL.md
        ├── references/
        ├── scripts/
        └── examples/
```

## Featured Skills

### Decision-Grade Research

Use this when the user has a decision to resolve, not merely a topic to learn. The skill turns the decision into hypotheses, evidence tracks, an adversarial falsification pass, and a conflict memo before writing a recommendation. Every conclusion must trace to an evidence ledger and be tagged as `observed`, `estimated`, or `assumed`.

Use it when:

- a user needs to choose between options under uncertainty
- sources may conflict and need explicit adjudication
- the output should be a decision report rather than a topic survey
- claims need source traceability and strength tags

The user provides:

- the decision question
- candidate options
- known constraints and criteria
- source URLs or local source files, if available

The agent produces:

- hypothesis tree
- parallel research tracks
- adversarial Track-D memo
- conflict memo
- evidence ledger
- final decision report and optional deck outline

Useful files:

- [Skill entry](skills/decision-grade-research/SKILL.md)
- [Human guide](docs/skills/decision-grade-research.md)
- [Evidence ledger contract](skills/decision-grade-research/references/evidence-ledger.md)
- [Search adapter](skills/decision-grade-research/references/search-adapter.md)
- [Worked example](skills/decision-grade-research/examples/fictional-market-entry-decision/README.md)

Example script:

```bash
python3 skills/decision-grade-research/scripts/search_sources.py \
  --provider none \
  --input skills/decision-grade-research/examples/fictional-market-entry-decision/source_candidates.json \
  --output-dir skills/decision-grade-research/output \
  --run-id 2026-06-04

python3 skills/decision-grade-research/scripts/build_evidence_ledger.py \
  --input skills/decision-grade-research/examples/fictional-market-entry-decision/research.json \
  --output-dir skills/decision-grade-research/output \
  --run-id 2026-06-04
```

### Project WIP Auditor

Use this when the user has many project directories and needs to understand what is actually active. The skill is read-only by default: it collects git history, file mtimes, README/TODO signals, and project structure, then emits a decision board.

Use it when:

- a user has many project folders and wants to know what is active or abandoned
- the agent is allowed to scan local directories read-only
- the desired output is a WIP decision board, not a calendar plan
- each project should receive a next action: `resume`, `ship`, `kill`, or `archive`

The user provides:

- one or more root directories to scan
- optional ignore rules
- optional date anchor for reproducible classification

The agent produces:

- scan JSON with filesystem and git signals
- Markdown WIP board
- JSON board for downstream use
- per-project state, action, and rationale

Useful files:

- [Skill entry](skills/project-wip-auditor/SKILL.md)
- [Human guide](docs/skills/project-wip-auditor.md)
- [Scan contract](skills/project-wip-auditor/references/scan-contract.md)
- [Worked example](skills/project-wip-auditor/examples/synthetic-workspace/README.md)

Example scripts:

```bash
python3 skills/project-wip-auditor/scripts/scan_projects.py \
  --root /path/to/project-root \
  --output-dir skills/project-wip-auditor/output

python3 skills/project-wip-auditor/scripts/build_wip_board.py \
  --input skills/project-wip-auditor/output/2026-06-04-scan.json \
  --as-of 2026-06-04 \
  --output-dir skills/project-wip-auditor/output
```

### Pre-mortem Red Team

Use this when the user already has a plan, launch, strategy, or decision and wants to surface failure modes before committing. It assumes the plan failed, attacks assumptions, ranks risks by likelihood and impact, and attaches thresholds plus mitigations.

Use it when:

- a user has a concrete plan or launch to stress-test
- assumptions need to be made explicit and attacked
- the user wants early-warning indicators, not just a risk list
- the output should improve the plan before commitment

The user provides:

- plan summary
- decision horizon
- known assumptions
- success criteria and constraints

The agent produces:

- pre-mortem failure scenarios
- red-team assumption attack
- ranked failure-mode table
- monitoring thresholds
- mitigation packages
- residual risk statement
- optional evidence check for fact-sensitive assumptions

Useful files:

- [Skill entry](skills/premortem-redteam/SKILL.md)
- [Human guide](docs/skills/premortem-redteam.md)
- [Pre-mortem protocol](skills/premortem-redteam/references/premortem-protocol.md)
- [Worked example](skills/premortem-redteam/examples/fictional-launch-premortem/README.md)

Example script:

```bash
python3 skills/decision-grade-research/scripts/search_sources.py \
  --provider tavily \
  --query "AI note taking app churn risk independent consultants" \
  --output-dir skills/premortem-redteam/output \
  --run-id 2026-06-04

python3 skills/premortem-redteam/scripts/generate_html_report.py \
  --input skills/premortem-redteam/examples/fictional-launch-premortem/analysis.json \
  --output-dir skills/premortem-redteam/output \
  --run-id 2026-06-04
```

### all2md

Use this when the user has a folder of mixed source materials and needs clean Markdown before analysis. The skill routes documents, PDFs, screenshots, scanned images, audio, and video through available local tools, mirrors the source folder structure, and writes `INDEX.md` plus `manifest.json` so downstream agents can trace every converted file.

Use it when:

- a research or diligence package contains mixed file types
- local conversion tools are available or can be probed
- output needs to preserve source-relative paths
- failures and parser choices should be auditable

The user provides:

- one or more source files or directories
- optional parser preferences such as PDF, image, or ASR mode
- optional output location

The agent produces:

- converted Markdown files
- `INDEX.md`
- `manifest.json`
- parser and quality-check summary
- rerun recommendations for failed or weak conversions

Useful files:

- [Skill entry](skills/all2md/SKILL.md)
- [Human guide](docs/skills/all2md.md)
- [Routing contract](skills/all2md/references/routing-contract.md)
- [Quality check](skills/all2md/references/quality-check.md)
- [Worked example](skills/all2md/examples/synthetic-source-package/README.md)

Example script:

```bash
python3 skills/all2md/scripts/convert_all.py source-package \
  --workers 4 \
  --pdf-workers 2 \
  --heavy-workers 1 \
  --asr-workers 1
```
