from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


class ValidationError(ValueError):
    pass


@dataclass
class ValidationResult:
    data: pd.DataFrame
    spec: dict[str, Any]
    summary: list[str]


def inspect_dataframe(df: pd.DataFrame) -> list[str]:
    lines = ["字段列表："]
    for column in df.columns:
        lines.append(f"- {column}: {_describe_series(df[column])}")
    return lines


def validate_chart(df: pd.DataFrame, spec: dict[str, Any]) -> ValidationResult:
    if df.empty:
        raise ValidationError("Input data is empty.")
    cleaned = df.copy()
    normalized_spec = dict(spec)
    normalized_spec.setdefault("data_notes", [])
    chart_type = normalized_spec.get("chart_type")
    if chart_type not in {"bar", "horizontal_bar", "grouped_bar", "stacked_bar", "line", "pie", "donut", "combo_bar_line", "scatter"}:
        raise ValidationError(f"Unsupported chart_type: {chart_type}")

    required = _required_fields(normalized_spec)
    _ensure_fields(cleaned, required)

    numeric_fields = _numeric_fields(normalized_spec)
    for field in numeric_fields:
        cleaned[field], notes = _coerce_numeric(cleaned[field], field)
        normalized_spec["data_notes"].extend(notes)

    relevant_fields = [field for field in required if field]
    before = len(cleaned)
    missing_by_field = cleaned[relevant_fields].isna().sum().to_dict()
    cleaned = cleaned.dropna(subset=relevant_fields)
    dropped = before - len(cleaned)
    if cleaned.empty:
        raise ValidationError("All rows were removed after dropping missing values in required fields.")

    summary = _summary_lines(cleaned, normalized_spec, missing_by_field, dropped)
    if chart_type in {"pie", "donut"}:
        total = float(cleaned[normalized_spec["value"]].sum())
        summary.append(f"- value 合计：{total:g}")
        if 90 <= total <= 110 and abs(total - 100) > 1:
            summary.append("- 提醒：value 看起来是百分比，但合计不等于 100。")
    if chart_type == "combo_bar_line":
        _infer_secondary_y(cleaned, normalized_spec, summary)

    return ValidationResult(cleaned, normalized_spec, summary)


def _required_fields(spec: dict[str, Any]) -> list[str]:
    chart_type = spec["chart_type"]
    if chart_type in {"bar", "line"}:
        return _compact([spec.get("x"), spec.get("y")])
    if chart_type in {"grouped_bar", "stacked_bar"}:
        return _compact([spec.get("x"), *_as_list(spec.get("y"))])
    if chart_type == "horizontal_bar":
        return _compact([spec.get("x"), spec.get("y")])
    if chart_type in {"pie", "donut"}:
        return _compact([spec.get("label"), spec.get("value")])
    if chart_type == "combo_bar_line":
        return _compact([spec.get("x"), spec.get("bar_y"), spec.get("line_y")])
    if chart_type == "scatter":
        return _compact([spec.get("x"), spec.get("y"), spec.get("size"), spec.get("color")])
    return []


def _numeric_fields(spec: dict[str, Any]) -> list[str]:
    chart_type = spec["chart_type"]
    if chart_type in {"bar", "line"}:
        return _compact([spec.get("y")])
    if chart_type in {"grouped_bar", "stacked_bar"}:
        return _compact(_as_list(spec.get("y")))
    if chart_type == "horizontal_bar":
        return _compact([spec.get("x")])
    if chart_type in {"pie", "donut"}:
        return _compact([spec.get("value")])
    if chart_type == "combo_bar_line":
        return _compact([spec.get("bar_y"), spec.get("line_y")])
    if chart_type == "scatter":
        return _compact([spec.get("x"), spec.get("y"), spec.get("size")])
    return []


def _ensure_fields(df: pd.DataFrame, fields: list[str]) -> None:
    if not fields:
        raise ValidationError("No chart fields were specified. Please provide explicit fields such as x=年份,y=收入.")
    missing = [field for field in fields if field not in df.columns]
    if missing:
        available = ", ".join(map(str, df.columns))
        raise ValidationError(f"Missing field(s): {', '.join(missing)}. Available fields: {available}")


def _coerce_numeric(series: pd.Series, field: str) -> tuple[pd.Series, list[str]]:
    notes: list[str] = []
    if pd.api.types.is_numeric_dtype(series):
        return series, notes
    text = series.astype(str).str.strip()
    has_percent = text.str.endswith("%", na=False).any()
    text = text.str.replace(",", "", regex=False)
    if has_percent:
        text = text.str.rstrip("%")
    coerced = pd.to_numeric(text, errors="coerce")
    if coerced.isna().any() and series.notna().any():
        bad_count = int(coerced.isna().sum())
        notes.append(f"{field}: {bad_count} value(s) could not be converted to numeric and will be dropped if required.")
    if has_percent:
        notes.append(f"{field}: percent strings were converted to numeric percentage points, e.g. 12% -> 12.")
    if coerced.notna().sum() == 0:
        raise ValidationError(f"Field {field} is not numeric and cannot be safely converted.")
    return coerced, notes


def _summary_lines(df: pd.DataFrame, spec: dict[str, Any], missing_by_field: dict[str, int], dropped: int) -> list[str]:
    lines = ["数据校验通过："]
    chart_type = spec["chart_type"]
    if spec.get("x"):
        if chart_type == "horizontal_bar":
            lines.append(f"- x 字段：{spec['x']}，数值型")
        else:
            lines.append(f"- x 字段：{spec['x']}，{df[spec['x']].nunique()} 个唯一值")
    if spec.get("y"):
        if chart_type == "horizontal_bar":
            lines.append(f"- y 字段：{spec['y']}，{df[spec['y']].nunique()} 个唯一值")
        elif chart_type in {"grouped_bar", "stacked_bar"}:
            lines.append(f"- y 字段：{', '.join(_as_list(spec['y']))}，均为数值型")
        else:
            lines.append(f"- y 字段：{spec['y']}，数值型")
    if spec.get("value"):
        lines.append(f"- value 字段：{spec['value']}，数值型")
    if chart_type == "combo_bar_line":
        lines.append(f"- bar_y 字段：{spec['bar_y']}，数值型")
        lines.append(f"- line_y 字段：{spec['line_y']}，数值型")
    lines.append(f"- 数据行数：{len(df)}")
    lines.append(f"- 缺失值：{sum(missing_by_field.values())}")
    if dropped:
        lines.append(f"- 已忽略缺失行：{dropped}")
    for note in spec.get("data_notes", []):
        lines.append(f"- 数据处理：{note}")
    lines.append(f"- 输出格式：{', '.join(spec.get('output_formats', ['svg', 'png']))}")
    return lines


def _infer_secondary_y(df: pd.DataFrame, spec: dict[str, Any], summary: list[str]) -> None:
    bar = df[spec["bar_y"]].abs().max()
    line = df[spec["line_y"]].abs().max()
    if line == 0 or bar == 0:
        spec["secondary_y"] = bool(spec.get("secondary_y", True))
        return
    ratio = max(bar, line) / min(bar, line)
    if ratio >= 5:
        spec["secondary_y"] = True
        summary.append("- 组合图：两个指标量级差异较大，启用双轴。")
    else:
        spec["secondary_y"] = bool(spec.get("secondary_y", False))


def _describe_series(series: pd.Series) -> str:
    if pd.api.types.is_integer_dtype(series):
        return "int"
    if pd.api.types.is_float_dtype(series):
        return "float"
    text = series.dropna().astype(str).str.strip()
    if not text.empty and text.str.endswith("%").any():
        return "percent-like string"
    if pd.to_numeric(text.str.replace(",", "", regex=False).str.rstrip("%"), errors="coerce").notna().all():
        return "numeric-like string"
    return "string"


def _compact(values: list[Any]) -> list[str]:
    return [str(value) for value in values if value not in (None, "")]


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if value in (None, ""):
        return []
    return [value]
