from __future__ import annotations

import re
from pathlib import Path
from typing import Any


CHART_KEYWORDS = [
    ("combo_bar_line", ["组合图", "柱状图+折线图", "柱线", "收入和利润率组合"]),
    ("stacked_bar", ["堆叠柱状图", "堆积柱状图", "堆叠柱形图", "堆积柱形图"]),
    ("grouped_bar", ["分组柱状图", "簇状柱状图", "并列柱状图", "多系列柱状图", "分组柱形图", "簇状柱形图"]),
    ("horizontal_bar", ["横向条形图", "条形图", "横向"]),
    ("donut", ["环形图", "甜甜圈"]),
    ("pie", ["饼图"]),
    ("scatter", ["散点图"]),
    ("line", ["折线图"]),
    ("bar", ["柱状图", "柱形图"]),
]

FIELD_ALIASES = {
    "标题": "title",
    "title": "title",
    "输出名": "output_name",
    "文件名": "output_name",
    "output": "output_name",
    "output_name": "output_name",
    "x": "x",
    "X": "x",
    "y": "y",
    "Y": "y",
    "label": "label",
    "value": "value",
    "bar_y": "bar_y",
    "line_y": "line_y",
    "color": "color",
    "size": "size",
}


class PromptParseError(ValueError):
    pass


def parse_formats(raw: str | None) -> list[str]:
    if not raw:
        return ["svg", "png"]
    formats = [item.strip().lower().lstrip(".") for item in raw.split(",") if item.strip()]
    invalid = sorted(set(formats) - {"svg", "png"})
    if invalid:
        raise PromptParseError(f"Unsupported output format(s): {', '.join(invalid)}. Only svg,png are supported in v1.")
    return formats or ["svg", "png"]


def parse_prompt(prompt: str, output_name: str | None = None, formats: list[str] | None = None) -> dict[str, Any]:
    if not prompt or not prompt.strip():
        raise PromptParseError("Prompt is required unless --spec is provided.")

    spec: dict[str, Any] = {
        "chart_type": _detect_chart_type(prompt),
        "title": None,
        "output_name": output_name,
        "output_formats": formats or ["svg", "png"],
        "theme": "consulting",
        "data_notes": [],
    }
    spec.update(_parse_assignments(prompt))
    _apply_prompt_inference(spec)

    if output_name:
        spec["output_name"] = output_name
    if not spec.get("output_name"):
        spec["output_name"] = _default_output_name(spec)
    if not spec.get("title"):
        spec["title"] = _default_title(spec)
    return spec


def normalize_spec(spec: dict[str, Any], output_name: str | None = None, formats: list[str] | None = None) -> dict[str, Any]:
    result = dict(spec)
    result.setdefault("theme", "consulting")
    result.setdefault("data_notes", [])
    if output_name:
        result["output_name"] = output_name
    result.setdefault("output_name", _default_output_name(result))
    if formats:
        result["output_formats"] = formats
    result.setdefault("output_formats", ["svg", "png"])
    result.setdefault("title", _default_title(result))
    return result


def _detect_chart_type(prompt: str) -> str:
    for chart_type, words in CHART_KEYWORDS:
        if any(word in prompt for word in words):
            return chart_type
    raise PromptParseError("Unable to detect chart type. Please include 柱状图/折线图/饼图/环形图/组合图/散点图.")


def _parse_assignments(prompt: str) -> dict[str, Any]:
    values: dict[str, Any] = {}
    keys = "|".join(re.escape(key) for key in sorted(FIELD_ALIASES, key=len, reverse=True))
    pattern = re.compile(rf"(?P<key>{keys})\s*[=:：]\s*(?P<value>.*?)(?=([,，;；]\s*(?:{keys})\s*[=:：])|$)")
    for match in pattern.finditer(prompt):
        key = FIELD_ALIASES[match.group("key")]
        value: Any = match.group("value").strip().strip(",，;； \n").strip('"').strip("'")
        if key == "y" and _looks_like_list(value):
            value = _split_list(value)
        if value:
            values[key] = value
    return values


def _apply_prompt_inference(spec: dict[str, Any]) -> None:
    chart_type = spec["chart_type"]
    if chart_type == "combo_bar_line":
        if "bar_y" not in spec and "y" in spec:
            spec["bar_y"] = spec["y"]
        spec.setdefault("bar_label", spec.get("bar_y"))
        spec.setdefault("line_label", spec.get("line_y"))
        spec.setdefault("secondary_y", True)
    elif chart_type in {"pie", "donut"}:
        if "label" not in spec and "x" in spec:
            spec["label"] = spec["x"]
        if "value" not in spec and "y" in spec:
            spec["value"] = spec["y"]
    elif chart_type == "horizontal_bar":
        if "x" in spec and "y" in spec:
            return
    elif chart_type in {"grouped_bar", "stacked_bar"}:
        if isinstance(spec.get("y"), str):
            spec["y"] = _split_list(spec["y"])


def _default_output_name(spec: dict[str, Any]) -> str:
    chart_type = spec.get("chart_type", "chart")
    stem = str(spec.get("title") or chart_type)
    ascii_stem = re.sub(r"[^A-Za-z0-9_\-]+", "_", stem).strip("_").lower()
    if not ascii_stem:
        ascii_stem = chart_type
    if chart_type not in ascii_stem:
        ascii_stem = f"{ascii_stem}_{chart_type}"
    return ascii_stem


def _default_title(spec: dict[str, Any]) -> str:
    chart_type = spec.get("chart_type", "chart")
    if chart_type == "combo_bar_line":
        return f"{spec.get('bar_y', '指标1')}与{spec.get('line_y', '指标2')}变化"
    if chart_type in {"grouped_bar", "stacked_bar"}:
        return "多指标对比"
    if chart_type in {"pie", "donut"}:
        return f"{spec.get('value', '数值')}结构"
    if spec.get("y"):
        return f"{spec['y']}趋势"
    return Path(spec.get("output_name", "chart")).stem


def _looks_like_list(value: str) -> bool:
    return any(sep in value for sep in [",", "，", "/", "、", "|"])


def _split_list(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"[,，/、|]+", value) if item.strip()]
