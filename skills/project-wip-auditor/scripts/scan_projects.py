#!/usr/bin/env python3
"""Scan project roots and emit decision-useful WIP signals as JSON.

This scanner is read-only. It treats each immediate subdirectory of every root as
a candidate project, then separates noisy freshness from meaningful work signals.
Generated images, caches, build folders, and bulky exports can make a project look
"active" even when no real project decision is needed; this script records those
signals separately instead of blindly trusting newest mtime.

Example:
    python3 scan_projects.py --root ~/Desktop/Project --output-dir skills/project-wip-auditor/output
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", ".idea", ".vscode",
    "dist", "build", ".next", ".cache", ".pytest_cache", "tmp", "temp",
}
GENERATED_DIRS = {
    "assets", "asset", "exports", "export", "outputs", "output", "reports",
    "downloads", "download", "final", "logs", "screenshots", "frames_png",
}
NOISY_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".mp4", ".mov", ".mp3",
    ".wav", ".pdf", ".pptx", ".docx", ".xlsx", ".zip", ".tar", ".gz",
}
MEANINGFUL_EXTS = {
    ".md", ".txt", ".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".json",
    ".yaml", ".yml", ".toml", ".html", ".css", ".sql", ".sh", ".csv",
}
README_NAMES = {"readme", "readme.md", "readme.rst", "readme.txt", "agents.md", "agent.md", "claude.md"}
TODO_NAMES = {"todo", "todo.md", "todo.txt"}


def iso_date(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat() if ts else None


def git_info(project: Path):
    if not (project / ".git").exists():
        return {"is_git": False, "last_commit": None, "last_commit_subject": None, "dirty": None}
    info = {"is_git": True, "last_commit": None, "last_commit_subject": None, "dirty": None}
    try:
        out = subprocess.run(
            ["git", "-C", str(project), "log", "-1", "--format=%cI%x00%s"],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=10,
        )
        if out.returncode == 0 and out.stdout.strip():
            raw_date, _, subject = out.stdout.strip().partition("\x00")
            info["last_commit"] = raw_date[:10]
            info["last_commit_subject"] = subject
        status = subprocess.run(
            ["git", "-C", str(project), "status", "--short"],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=10,
        )
        if status.returncode == 0:
            info["dirty"] = bool(status.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    return info


def in_generated_path(path: Path, root: Path):
    parts = {p.lower() for p in path.relative_to(root).parts[:-1]}
    return bool(parts & GENERATED_DIRS)


def scan_project(project: Path, ignore_dirs: set):
    newest_any = 0.0
    newest_meaningful = 0.0
    newest_noise = 0.0
    newest_any_path = ""
    newest_meaningful_path = ""
    newest_noise_path = ""
    file_count = 0
    meaningful_count = 0
    noisy_count = 0
    size_bytes = 0
    readmes = []
    has_todo = False

    for dirpath, dirnames, filenames in os.walk(project):
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs and not d.startswith(".")]
        for name in filenames:
            if name.startswith(".") or name == ".DS_Store":
                continue
            path = Path(dirpath) / name
            try:
                st = path.stat()
            except OSError:
                continue
            rel = path.relative_to(project).as_posix()
            lower = name.lower()
            ext = path.suffix.lower()
            generated = in_generated_path(path, project)
            noisy = generated or ext in NOISY_EXTS
            meaningful = ext in MEANINGFUL_EXTS and not noisy

            file_count += 1
            size_bytes += st.st_size
            if st.st_mtime > newest_any:
                newest_any = st.st_mtime
                newest_any_path = rel
            if noisy:
                noisy_count += 1
                if st.st_mtime > newest_noise:
                    newest_noise = st.st_mtime
                    newest_noise_path = rel
            if meaningful:
                meaningful_count += 1
                if st.st_mtime > newest_meaningful:
                    newest_meaningful = st.st_mtime
                    newest_meaningful_path = rel
            if lower in README_NAMES:
                readmes.append(rel)
            if lower in TODO_NAMES or "todo" in lower:
                has_todo = True

    signals = {
        "name": project.name,
        "path": str(project),
        "file_count": file_count,
        "meaningful_file_count": meaningful_count,
        "noisy_file_count": noisy_count,
        "size_bytes": size_bytes,
        "newest_mtime": iso_date(newest_any),
        "newest_mtime_path": newest_any_path,
        "meaningful_mtime": iso_date(newest_meaningful),
        "meaningful_mtime_path": newest_meaningful_path,
        "noise_mtime": iso_date(newest_noise),
        "noise_mtime_path": newest_noise_path,
        "has_readme": bool(readmes),
        "readme_paths": readmes[:6],
        "has_todo": has_todo,
    }
    signals.update(git_info(project))
    return signals


def scan_root(root: Path, ignore_dirs: set):
    projects = []
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name.startswith(".") or child.name in ignore_dirs:
            continue
        projects.append(scan_project(child, ignore_dirs))
    return projects


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--root", action="append", default=[], metavar="DIR", help="Root directory to scan. Repeatable.")
    parser.add_argument("--ignore", action="append", default=[], metavar="NAME", help="Extra directory name to ignore. Repeatable.")
    parser.add_argument("--output", metavar="FILE", help="Write JSON here instead of stdout.")
    parser.add_argument("--output-dir", metavar="DIR", help="Write scan.json into this directory.")
    parser.add_argument("--run-id", metavar="ID", help="Filename prefix for output-dir mode (default: scan date).")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if not args.root:
        print("error: provide at least one --root DIR", file=sys.stderr)
        return 2
    ignore_dirs = set(DEFAULT_IGNORE_DIRS) | set(args.ignore)
    projects = []
    roots = []
    for root in args.root:
        root_path = Path(root).expanduser()
        if not root_path.is_dir():
            print(f"warning: skipping missing root {root}", file=sys.stderr)
            continue
        roots.append(str(root_path))
        projects.extend(scan_root(root_path, ignore_dirs))
    payload = {
        "scanned_at": datetime.now(tz=timezone.utc).date().isoformat(),
        "roots": roots,
        "projects": projects,
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    output_path = None
    if args.output_dir:
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        run_id = args.run_id or payload["scanned_at"]
        output_path = out_dir / f"{run_id}-scan.json"
    elif args.output:
        output_path = Path(args.output)
    if output_path:
        output_path.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
