---
name: decision-grade-research
description: Turn a real decision under uncertainty into an auditable, decision-grade research report. Use when the user must choose between options and wants a hypothesis tree, parallel evidence tracks, an adversarial check that actively tries to falsify the leading answer, a conflict memo that adjudicates contradictory sources, and an evidence ledger where every claim traces to a source URL or file path. Do not use for topic tutorials, science-explainer essays, quick factual lookups, or generic "deep research" with no decision to resolve.
---

# Decision-Grade Research

## Use This Skill For

- turn "which option should I choose, and why?" into an auditable decision report, not an explainer essay
- build a hypothesis tree before searching, so research is driven by what would change the decision
- run parallel evidence tracks and an adversarial Track-D that tries to falsify the leading answer
- adjudicate contradictory sources in a conflict memo instead of averaging them away
- keep an evidence ledger where every claim is tagged `observed` / `estimated` / `assumed` and linked to a source
- optionally use a search adapter (Tavily, Brave, or local source-candidate JSON) to discover source candidates

## Do Not Route Here

- topic tutorials or study guides (use a tutorial/learning skill instead)
- quick factual lookups or single-question web search
- "deep research" requests with no actual decision to resolve
- final licensed medical, legal, or financial advice

## Default Workflow

1. Use `references/hypothesis-tree.md` to frame the decision, the candidate options, and the hypotheses whose truth would change the choice.
2. Use `references/search-adapter.md` if live discovery is needed; run `scripts/search_sources.py` with `--provider tavily`, `--provider brave`, or `--provider none`.
3. Use `references/research-tracks.md` to run parallel evidence tracks, capturing sources as you go.
4. Use `references/adversarial-track-d.md` to actively attack the leading answer — assume it is wrong and look for disconfirming evidence.
5. Use `references/conflict-adjudication.md` when sources disagree: surface the conflict, weigh source quality, and decide rather than blend.
6. Run `scripts/build_evidence_ledger.py` to assemble the evidence ledger from captured sources.
7. Use `references/evidence-ledger.md` to tag every claim `observed` / `estimated` / `assumed` and link it to a source URL or file path.
8. Use `references/output-contract.md` to produce the decision report: recommendation, option comparison, key evidence, open risks, and what would change the call.

## Core Rules

- the method is the product: hypothesis tree → tracks → adversarial check → conflict memo → ledger
- never present a conclusion that is not in the evidence ledger
- always run Track-D before finalizing; a recommendation with no disconfirming search is not decision-grade
- when sources conflict, adjudicate explicitly — never silently average or pick the convenient one
- tag every number and claim as `observed`, `estimated`, or `assumed`
- local-first and reproducible: prefer captured local copies of sources over volatile links
- search providers are optional adapters; never hard-code API keys or treat raw search results as evidence
- never publish private consulting archives or client materials; public examples use fictional decisions only

## Output Contract

- deliver a decision report, not a topic survey
- the report must include:
  - recommendation and the decision it answers
  - option comparison
  - hypothesis tree and which hypotheses were resolved
  - Track-D findings (what was attacked, what survived)
  - conflict memo for any contradictory sources
  - evidence ledger with source links and `observed/estimated/assumed` tags
  - open risks and the trigger that would change the recommendation
  - optional deck outline
