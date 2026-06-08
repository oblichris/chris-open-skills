from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd

from .parser import PromptParseError, normalize_spec, parse_formats, parse_prompt
from .renderer import render_chart
from .validator import ValidationError, inspect_dataframe, validate_chart


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    try:
        formats = parse_formats(args.format)
        df = load_data(args)
        if args.inspect:
            print("\n".join(inspect_dataframe(df)))
            return 0
        spec = load_spec(args, formats)
        validation = validate_chart(df, spec)
        print("\n".join(validation.summary))
        output_dir = create_run_output_dir(Path(args.output_dir))
        paths = render_chart(validation.data, validation.spec, output_dir)
        print("已生成：")
        for path in paths:
            print(f"- {path}")
        return 0
    except (PromptParseError, ValidationError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-chart", description="Generate consulting-style charts from local data.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", help="CSV or Excel file path.")
    source.add_argument("--data", help="Pasted CSV-like data.")
    parser.add_argument("--sheet", help="Excel sheet name.")
    parser.add_argument("--prompt", help="Simple natural-language prompt with explicit field assignments.")
    parser.add_argument("--spec", help="Path to a chart spec JSON file.")
    parser.add_argument("--inspect", action="store_true", help="Preview fields and inferred data types.")
    parser.add_argument("--format", default="svg,png", help="Comma-separated output formats. v1 supports svg,png.")
    parser.add_argument("--output", help="Output file stem. Overrides spec output_name.")
    parser.add_argument("--output-dir", default="output", help="Base output directory. A timestamped run folder is created inside it.")
    return parser


def load_data(args: argparse.Namespace) -> pd.DataFrame:
    if args.data:
        return pd.read_csv(StringIO(args.data.strip()))
    path = Path(args.input)
    if not path.exists():
        raise OSError(f"Input file does not exist: {path}")
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path, sheet_name=args.sheet or 0)
    raise ValueError(f"Unsupported input file type: {suffix}. Use CSV or Excel.")


def load_spec(args: argparse.Namespace, formats: list[str]) -> dict[str, Any]:
    if args.spec:
        raw = Path(args.spec).read_text(encoding="utf-8")
        return normalize_spec(json.loads(raw), output_name=args.output, formats=formats if args.format else None)
    if not args.prompt:
        raise PromptParseError("Provide --prompt, --spec, or --inspect.")
    return parse_prompt(args.prompt, output_name=args.output, formats=formats)


def create_run_output_dir(base: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    candidate = base / timestamp
    counter = 1
    while candidate.exists():
        candidate = base / f"{timestamp}_{counter:02d}"
        counter += 1
    candidate.mkdir(parents=True, exist_ok=False)
    return candidate


if __name__ == "__main__":
    raise SystemExit(main())
