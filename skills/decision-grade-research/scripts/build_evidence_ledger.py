#!/usr/bin/env python3
"""Render a decision-grade evidence ledger to Markdown and validate its integrity.

Reads the structured research JSON defined in references/evidence-ledger.md from --input or
stdin: the decision, the hypothesis tree, and the claims with their sources and strength
tags. Renders a Markdown ledger and reports validation warnings so thin evidence is visible
before the report is finalized.

Validation warnings:
  - a claim tagged 'observed' or 'estimated' with no source attached
  - a claim referencing a hypothesis id that does not exist in the tree
  - a load-bearing hypothesis with no supporting claim in the ledger

Warnings are surfaced, not auto-fixed. Exit code is 0 unless --strict is passed, in which
case any warning yields a non-zero exit (useful in CI gates).

Example:
    python3 build_evidence_ledger.py --input research.json --output-dir output --run-id 2026-06-04
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

SOURCED_STRENGTHS = {"observed", "estimated"}


def validate(data: dict):
    warnings = []
    hyps = {h.get("id"): h for h in data.get("hypotheses", [])}
    claims = data.get("claims", [])
    claimed_hyps = {c.get("hypothesis") for c in claims}

    for c in claims:
        cid = c.get("id", "?")
        if c.get("strength") in SOURCED_STRENGTHS and not c.get("sources"):
            warnings.append(f"{cid}: tagged '{c.get('strength')}' but has no source attached")
        if c.get("hypothesis") not in hyps:
            warnings.append(f"{cid}: references unknown hypothesis '{c.get('hypothesis')}'")

    for hid, h in hyps.items():
        if h.get("impact") == "high" and hid not in claimed_hyps:
            warnings.append(f"{hid}: load-bearing (high-impact) hypothesis has no supporting claim")

    return warnings


def render_markdown(data: dict, warnings):
    hyps = data.get("hypotheses", [])
    claims = data.get("claims", [])
    lines = ["# Evidence Ledger", ""]
    if data.get("decision"):
        lines += [f"**Decision:** {data['decision']}", ""]

    lines += ["## Hypotheses", "", "| ID | Impact | Status | Statement |", "| --- | --- | --- | --- |"]
    for h in hyps:
        lines.append(f"| {h.get('id','')} | {h.get('impact','')} | {h.get('status','')} | {h.get('statement','')} |")
    lines.append("")

    lines += ["## Claims", "", "| ID | Hyp | Strength | Statement | Sources |",
              "| --- | --- | --- | --- | --- |"]
    for c in claims:
        srcs = c.get("sources", [])
        rendered = "; ".join(
            f"[{s.get('title', s.get('ref',''))}]({s.get('ref','')})" + (f" ({s['date']})" if s.get("date") else "")
            for s in srcs
        ) or "—"
        lines.append(
            f"| {c.get('id','')} | {c.get('hypothesis','')} | {c.get('strength','')} "
            f"| {c.get('statement','')} | {rendered} |"
        )
    lines.append("")

    # strength mix summary
    mix = {}
    for c in claims:
        mix[c.get("strength", "untagged")] = mix.get(c.get("strength", "untagged"), 0) + 1
    if mix:
        summary = ", ".join(f"{k}: {v}" for k, v in sorted(mix.items()))
        lines += ["## Strength mix", "", summary, ""]

    lines += ["## Validation", ""]
    if warnings:
        lines += [f"- WARNING {w}" for w in warnings]
    else:
        lines.append("- No integrity warnings.")
    lines.append("")
    return "\n".join(lines)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--input", metavar="FILE", help="Research JSON file (default: stdin).")
    parser.add_argument("--output", metavar="FILE", help="Write the Markdown ledger here instead of stdout.")
    parser.add_argument("--output-dir", metavar="DIR", help="Write RUN-ID-evidence-ledger.md into this directory.")
    parser.add_argument("--run-id", metavar="ID", help="Filename prefix for output-dir mode (default: today's date).")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if any validation warning is raised.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    raw = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
    if not raw.strip():
        print("error: no research JSON provided on --input or stdin", file=sys.stderr)
        return 2
    data = json.loads(raw)
    warnings = validate(data)
    ledger = render_markdown(data, warnings)
    if args.output_dir:
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        run_id = args.run_id or date.today().isoformat()
        path = out_dir / f"{run_id}-evidence-ledger.md"
        path.write_text(ledger + "\n", encoding="utf-8")
        print(f"wrote {path}")
    elif args.output:
        Path(args.output).write_text(ledger + "\n", encoding="utf-8")
    else:
        print(ledger)
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
