#!/usr/bin/env python3
"""Turn project scan signals into a decision-useful WIP board.

The board intentionally avoids the naive "recent mtime means active" trap. It
uses meaningful text/code/config edits, git signals, documentation, and noise
ratio to separate real work from generated artifacts or scratch folders.

Example:
    python3 build_wip_board.py --input scan.json --as-of 2026-06-04 \
        --output-dir skills/project-wip-auditor/output
"""

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

STATE_ORDER = ["hot", "active", "cooling", "parked", "cold", "unclear"]
ACTION_ORDER = ["focus", "close_loop", "resume", "park", "archive", "drop"]


def parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date()


def days_since(value, as_of):
    if not value:
        return None
    return (as_of - parse_date(value)).days


def last_real_activity(project):
    """Prefer committed or meaningful edits over noisy generated mtimes."""
    candidates = [project.get("last_commit"), project.get("meaningful_mtime")]
    dates = [parse_date(c) for c in candidates if c]
    return max(dates).isoformat() if dates else project.get("newest_mtime")


def shape(project):
    meaningful = project.get("meaningful_file_count", 0)
    files = project.get("file_count", 0)
    has_readme = project.get("has_readme", False)
    noisy = project.get("noisy_file_count", 0)
    noise_ratio = noisy / files if files else 0
    if meaningful <= 3 and not has_readme:
        return "scratch"
    if noise_ratio >= 0.75 and meaningful < 12:
        return "artifact-heavy"
    if has_readme and meaningful >= 20:
        return "productized"
    if meaningful >= 20:
        return "substantial"
    if has_readme:
        return "documented"
    return "thin"


def classify(days, project_shape):
    if days is None:
        return "unclear"
    if days <= 2:
        return "hot"
    if days <= 7:
        return "active"
    if days <= 21:
        return "cooling"
    if days <= 90:
        return "parked"
    return "cold"


def triage(state, project_shape, project):
    has_readme = project.get("has_readme", False)
    dirty = project.get("dirty")
    name = project.get("name", "")
    if project_shape == "scratch":
        return "drop", "thin scratch folder; decide now or remove from the WIP surface"
    if project_shape == "artifact-heavy":
        return "close_loop", "mostly generated/assets; preserve the output or write the decision note, then stop treating it as active"
    if state == "hot":
        if project_shape in {"productized", "substantial"}:
            return "focus", "real work touched in the last 48h; choose whether this is one of the week's main bets"
        return "close_loop", "recent but under-documented; write the next action or park it"
    if state == "active":
        if dirty:
            return "close_loop", "recent git repo with uncommitted changes; commit, discard, or capture the stopping point"
        if project_shape in {"productized", "substantial", "documented"}:
            return "resume", "warm enough to resume without heavy context rebuilding"
        return "park", "warm but low-substance; keep only if it supports a current priority"
    if state == "cooling":
        if project_shape in {"productized", "substantial"}:
            return "park", "real work, but not current; write a restart note before context fades"
        return "archive", "cooling and low-substance; keep for record only"
    if state == "parked":
        if has_readme:
            return "archive", "documented but outside current momentum; archive or backlog explicitly"
        return "drop", "old enough and undocumented enough to leave the WIP board"
    if state == "cold":
        if project_shape in {"productized", "substantial"}:
            return "archive", "substantial historical work; archive for retrieval, not active attention"
        return "drop", "cold and thin; remove from active mental inventory"
    return "park", f"{name} has weak signals; inspect manually before deciding"


def evaluate(project, as_of):
    activity = last_real_activity(project)
    days = days_since(activity, as_of)
    project_shape = shape(project)
    state = classify(days, project_shape)
    action, rationale = triage(state, project_shape, project)
    noise_note = ""
    if project.get("newest_mtime") and project.get("meaningful_mtime") and project["newest_mtime"] != project["meaningful_mtime"]:
        noise_note = f"newest file is {project.get('newest_mtime_path')}, but meaningful signal is {project.get('meaningful_mtime_path')}"
    return {
        "name": project.get("name"),
        "path": project.get("path"),
        "state": state,
        "shape": project_shape,
        "action": action,
        "rationale": rationale,
        "last_real_activity": activity,
        "days_since": days,
        "meaningful_signal": project.get("meaningful_mtime_path") or project.get("last_commit_subject") or "",
        "noise_note": noise_note,
        "meaningful_file_count": project.get("meaningful_file_count", 0),
        "file_count": project.get("file_count", 0),
        "has_readme": project.get("has_readme", False),
        "is_git": project.get("is_git", False),
        "dirty": project.get("dirty"),
    }


def action_label(action):
    return {
        "focus": "make this a main workstream",
        "close_loop": "capture the stopping point or finish the artifact",
        "resume": "resume only if it matches the current goal",
        "park": "park deliberately",
        "archive": "archive for retrieval",
        "drop": "remove from active attention",
    }.get(action, action)


def render_project_bullets(lines, rows):
    for r in rows:
        lines.append(f"- **{r['name']}** — `{r['state']}` / `{r['shape']}`, last real activity `{r['last_real_activity'] or 'unknown'}`.")
        lines.append(f"  - Recommendation: **{action_label(r['action'])}**.")
        lines.append(f"  - Why: {r['rationale']}.")
        if r["meaningful_signal"]:
            lines.append(f"  - Evidence: `{r['meaningful_signal']}`.")
        if r["noise_note"]:
            lines.append(f"  - Noise check: {r['noise_note']}.")


def render_section(lines, title, rows, intro):
    lines.append(f"## {title}")
    lines.append("")
    lines.append(intro)
    lines.append("")
    if not rows:
        lines.append("_None._")
        lines.append("")
        return
    render_project_bullets(lines, rows)
    lines.append("")


def render_markdown(rows, as_of, roots):
    focus = [r for r in rows if r["action"] == "focus"]
    close_loop = [r for r in rows if r["action"] == "close_loop"]
    resume = [r for r in rows if r["action"] == "resume"]
    park_archive = [r for r in rows if r["action"] in {"park", "archive"}]
    drop = [r for r in rows if r["action"] == "drop"]
    focus_names = ", ".join(r["name"] for r in focus[:3]) or "none"
    close_names = ", ".join(r["name"] for r in close_loop[:5]) or "none"

    lines = ["# Project WIP Audit", ""]
    lines.append(f"_As of {as_of.isoformat()}; scanned roots: {', '.join(roots) or 'n/a'}._")
    lines.append("")
    counts = {a: sum(1 for r in rows if r["action"] == a) for a in ACTION_ORDER}
    lines.append("## Executive Recommendation")
    lines.append("")
    lines.append(f"- Treat this as a decision board, not a freshness report: `{len(rows)}` projects scanned.")
    lines.append(f"- Main focus should be capped at 2-3 workstreams. Current strongest focus candidates: **{focus_names}**.")
    lines.append(f"- Close open loops before starting more work. Highest-priority close-loop items: **{close_names}**.")
    lines.append("- Move park/archive/drop items out of daily attention unless they directly support the chosen focus.")
    lines.append("")

    lines.append("## Action Counts")
    lines.append("")
    lines.append("`" + " · ".join(f"{a}: {counts[a]}" for a in ACTION_ORDER) + "`")
    lines.append("")

    render_section(lines, "1. Focus Candidates", focus, "Choose at most a few. These are not all commitments; they are the short list for this week's main bets.")
    render_section(lines, "2. Close The Loop", close_loop, "These are the most dangerous attention leaks: recently touched, artifact-heavy, dirty, or under-documented.")
    render_section(lines, "3. Resume Only If It Matches The Current Goal", resume, "These are warm enough to restart, but should not compete with the main bets by default.")
    render_section(lines, "4. Park Or Archive", park_archive, "Keep these out of daily attention. Add a restart note only when the project has future value.")
    render_section(lines, "5. Drop From Active Attention", drop, "These are thin or scratch-like. They may remain on disk, but should leave the mental WIP board.")
    return "\n".join(lines)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--input", metavar="FILE", help="Scan JSON file (default: stdin).")
    parser.add_argument("--as-of", metavar="YYYY-MM-DD", help="Evaluate relative to this date (default: today).")
    parser.add_argument("--json-out", metavar="FILE", help="Also write the evaluated board as JSON here.")
    parser.add_argument("--output-dir", metavar="DIR", help="Write dated audit Markdown and JSON into this directory.")
    parser.add_argument("--run-id", metavar="ID", help="Filename prefix for output-dir mode (default: --as-of date).")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    raw = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
    if not raw.strip():
        print("error: no scan JSON provided on --input or stdin", file=sys.stderr)
        return 2
    data = json.loads(raw)
    as_of = parse_date(args.as_of) if args.as_of else date.today()
    rows = [evaluate(p, as_of) for p in data.get("projects", [])]
    rows.sort(key=lambda r: (ACTION_ORDER.index(r["action"]), r["days_since"] if r["days_since"] is not None else 999, r["name"]))
    board_json = {"as_of": as_of.isoformat(), "roots": data.get("roots", []), "board": rows}
    board_md = render_markdown(rows, as_of, data.get("roots", []))
    if args.output_dir:
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        run_id = args.run_id or as_of.isoformat()
        json_path = out_dir / f"{run_id}-wip-audit.json"
        md_path = out_dir / f"{run_id}-wip-audit.md"
        json_path.write_text(json.dumps(board_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        md_path.write_text(board_md + "\n", encoding="utf-8")
        print(f"wrote {md_path}")
    else:
        if args.json_out:
            Path(args.json_out).write_text(json.dumps(board_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(board_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
