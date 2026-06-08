from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .themes import Theme, apply_theme, get_theme


def render_chart(df: pd.DataFrame, spec: dict[str, Any], output_dir: Path) -> list[Path]:
    theme = get_theme(spec.get("theme"))
    apply_theme(theme)
    output_dir.mkdir(parents=True, exist_ok=True)

    chart_type = spec["chart_type"]
    if chart_type == "bar":
        fig = _bar(df, spec, theme)
    elif chart_type == "grouped_bar":
        fig = _grouped_bar(df, spec, theme)
    elif chart_type == "stacked_bar":
        fig = _stacked_bar(df, spec, theme)
    elif chart_type == "horizontal_bar":
        fig = _horizontal_bar(df, spec, theme)
    elif chart_type == "line":
        fig = _line(df, spec, theme)
    elif chart_type == "pie":
        fig = _pie(df, spec, theme, donut=False)
    elif chart_type == "donut":
        fig = _pie(df, spec, theme, donut=True)
    elif chart_type == "combo_bar_line":
        fig = _combo(df, spec, theme)
    elif chart_type == "scatter":
        fig = _scatter(df, spec, theme)
    else:
        raise ValueError(f"Unsupported chart_type: {chart_type}")

    output_name = spec["output_name"]
    paths: list[Path] = []
    for fmt in spec.get("output_formats", ["svg", "png"]):
        path = output_dir / f"{output_name}.{fmt}"
        fig.savefig(path, format=fmt, dpi=theme.dpi)
        paths.append(path)
    spec_path = output_dir / f"{output_name}.spec.json"
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths.append(spec_path)
    plt.close(fig)
    return paths


def _bar(df: pd.DataFrame, spec: dict[str, Any], theme: Theme):
    data = _sort_for_display(df, spec)
    fig, ax = _figure(theme)
    ax.bar(data[spec["x"]].astype(str), data[spec["y"]], color=theme.colors[0], width=0.62)
    _style_cartesian(ax, theme, spec["title"], spec.get("x"), spec.get("y"))
    _add_value_labels(ax, data[spec["y"]], theme)
    fig.tight_layout(pad=2)
    return fig


def _horizontal_bar(df: pd.DataFrame, spec: dict[str, Any], theme: Theme):
    data = df.copy()
    x_field, y_field = spec["x"], spec["y"]
    data = data.sort_values(x_field, ascending=True)
    fig, ax = _figure(theme)
    ax.barh(data[y_field].astype(str), data[x_field], color=theme.colors[0], height=0.56)
    _style_cartesian(ax, theme, spec["title"], x_field, y_field, x_grid=True)
    for index, value in enumerate(data[x_field]):
        ax.text(value, index, f" {value:g}", va="center", ha="left", fontsize=theme.value_label_size, color=theme.muted_text)
    fig.tight_layout(pad=2)
    return fig


def _grouped_bar(df: pd.DataFrame, spec: dict[str, Any], theme: Theme):
    data = _sort_for_display(df, spec)
    y_fields = _as_list(spec["y"])
    x = np.arange(len(data))
    group_width = 0.72
    bar_width = group_width / max(len(y_fields), 1)
    fig, ax = _figure(theme)
    for index, field in enumerate(y_fields):
        offset = (index - (len(y_fields) - 1) / 2) * bar_width
        ax.bar(
            x + offset,
            data[field],
            width=bar_width * 0.88,
            color=theme.colors[index % len(theme.colors)],
            label=field,
        )
    ax.set_xticks(x)
    ax.set_xticklabels(data[spec["x"]].astype(str))
    _style_cartesian(ax, theme, spec["title"], spec.get("x"), spec.get("value_label") or "数值")
    ax.legend(loc="upper left", frameon=False, ncols=min(len(y_fields), 4))
    ax.set_ylim(top=max(data[y_fields].max().max(), 1) * 1.18)
    fig.tight_layout(pad=2)
    return fig


def _stacked_bar(df: pd.DataFrame, spec: dict[str, Any], theme: Theme):
    data = _sort_for_display(df, spec)
    y_fields = _as_list(spec["y"])
    x_labels = data[spec["x"]].astype(str)
    bottoms = np.zeros(len(data))
    fig, ax = _figure(theme)
    for index, field in enumerate(y_fields):
        values = data[field].to_numpy()
        ax.bar(
            x_labels,
            values,
            bottom=bottoms,
            width=0.62,
            color=theme.colors[index % len(theme.colors)],
            label=field,
        )
        bottoms = bottoms + values
    _style_cartesian(ax, theme, spec["title"], spec.get("x"), spec.get("value_label") or "数值")
    ax.legend(loc="upper left", frameon=False, ncols=min(len(y_fields), 4))
    ax.set_ylim(top=max(bottoms.max(), 1) * 1.16)
    fig.tight_layout(pad=2)
    return fig


def _line(df: pd.DataFrame, spec: dict[str, Any], theme: Theme):
    data = _sort_for_display(df, spec)
    fig, ax = _figure(theme)
    ax.plot(data[spec["x"]].astype(str), data[spec["y"]], color=theme.colors[0], linewidth=2.6, marker="o", markersize=6)
    _style_cartesian(ax, theme, spec["title"], spec.get("x"), spec.get("y"))
    _add_value_labels(ax, data[spec["y"]], theme, offset=8)
    fig.tight_layout(pad=2)
    return fig


def _pie(df: pd.DataFrame, spec: dict[str, Any], theme: Theme, donut: bool):
    data = df.copy()
    fig, ax = _figure(theme)
    wedges, texts, autotexts = ax.pie(
        data[spec["value"]],
        labels=data[spec["label"]].astype(str),
        colors=theme.colors,
        startangle=90,
        counterclock=False,
        autopct="%1.0f%%",
        pctdistance=0.74 if donut else 0.68,
        labeldistance=1.08,
        wedgeprops={"linewidth": 1, "edgecolor": "white"},
    )
    for text in texts + autotexts:
        text.set_fontsize(theme.legend_size)
        text.set_color(theme.text)
    if donut:
        centre = plt.Circle((0, 0), 0.54, fc="white")
        ax.add_artist(centre)
    ax.set_title(spec["title"], loc="left", pad=16)
    ax.axis("equal")
    fig.tight_layout(pad=2)
    return fig


def _combo(df: pd.DataFrame, spec: dict[str, Any], theme: Theme):
    data = _sort_for_display(df, spec)
    fig, ax = _figure(theme)
    x_labels = data[spec["x"]].astype(str)
    bar = ax.bar(x_labels, data[spec["bar_y"]], color=theme.colors[0], width=0.62, label=spec.get("bar_label") or spec["bar_y"])
    _style_cartesian(ax, theme, spec["title"], spec.get("x"), spec.get("bar_y"))

    if spec.get("secondary_y", True):
        line_ax = ax.twinx()
        line_ax.plot(x_labels, data[spec["line_y"]], color=theme.accent, linewidth=2.6, marker="o", label=spec.get("line_label") or spec["line_y"])
        line_ax.set_ylabel(spec.get("line_label") or spec["line_y"], color=theme.text, fontsize=theme.label_size)
        line_ax.tick_params(axis="y", colors=theme.muted_text)
        line_ax.spines["top"].set_visible(False)
        line_ax.spines["right"].set_color(theme.axis)
        handles = [bar, line_ax.lines[0]]
        labels = [handle.get_label() for handle in handles]
        ax.legend(handles, labels, loc="upper left", frameon=False, ncols=2)
    else:
        ax.plot(x_labels, data[spec["line_y"]], color=theme.accent, linewidth=2.6, marker="o", label=spec.get("line_label") or spec["line_y"])
        ax.legend(loc="upper left", frameon=False, ncols=2)
    fig.tight_layout(pad=2)
    return fig


def _scatter(df: pd.DataFrame, spec: dict[str, Any], theme: Theme):
    fig, ax = _figure(theme)
    size = df[spec["size"]] if spec.get("size") else 76
    if spec.get("color"):
        categories = list(pd.unique(df[spec["color"]]))
        for index, category in enumerate(categories):
            subset = df[df[spec["color"]] == category]
            ax.scatter(
                subset[spec["x"]],
                subset[spec["y"]],
                s=size if isinstance(size, int) else subset[spec["size"]],
                color=theme.colors[index % len(theme.colors)],
                label=str(category),
                alpha=0.9,
                edgecolors="white",
                linewidth=0.8,
            )
        ax.legend(loc="upper left", frameon=False, title=spec["color"])
    else:
        ax.scatter(df[spec["x"]], df[spec["y"]], s=size, color=theme.colors[0], alpha=0.9, edgecolors="white", linewidth=0.8)
    _style_cartesian(ax, theme, spec["title"], spec.get("x"), spec.get("y"))
    fig.tight_layout(pad=2)
    return fig


def _figure(theme: Theme):
    return plt.subplots(figsize=theme.figsize, dpi=theme.dpi)


def _style_cartesian(ax, theme: Theme, title: str, xlabel: str | None, ylabel: str | None, x_grid: bool = False) -> None:
    ax.set_title(title, loc="left", pad=18)
    if xlabel:
        ax.set_xlabel(xlabel, labelpad=10)
    if ylabel:
        ax.set_ylabel(ylabel, labelpad=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(theme.axis)
    ax.spines["bottom"].set_color(theme.axis)
    ax.grid(axis="x" if x_grid else "y", color=theme.grid, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", rotation=0)


def _add_value_labels(ax, values: pd.Series, theme: Theme, offset: int = 4) -> None:
    max_value = max(values.max(), 1)
    for index, value in enumerate(values):
        ax.annotate(
            f"{value:g}",
            xy=(index, value),
            xytext=(0, offset),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=theme.value_label_size,
            color=theme.muted_text,
        )
    ax.set_ylim(top=max_value * 1.16)


def _sort_for_display(df: pd.DataFrame, spec: dict[str, Any]) -> pd.DataFrame:
    data = df.copy()
    if spec.get("sort") == "desc" and spec.get("y"):
        return data.sort_values(spec["y"], ascending=False)
    if spec.get("sort") == "asc" and spec.get("y"):
        return data.sort_values(spec["y"], ascending=True)
    return data


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, tuple):
        return [str(item) for item in value]
    return [str(value)]
