from __future__ import annotations

from dataclasses import dataclass

import matplotlib.pyplot as plt


@dataclass(frozen=True)
class Theme:
    name: str
    figsize: tuple[float, float]
    dpi: int
    fonts: list[str]
    text: str
    muted_text: str
    grid: str
    axis: str
    colors: list[str]
    accent: str
    title_size: int
    label_size: int
    tick_size: int
    legend_size: int
    value_label_size: int


CONSULTING = Theme(
    name="consulting",
    figsize=(6, 3.375),
    dpi=200,
    fonts=[
        "Microsoft YaHei",
        "PingFang SC",
        "Lantinghei SC",
        "Heiti SC",
        "Heiti TC",
        "Arial Unicode MS",
        "Noto Sans CJK SC",
        "Arial",
        "Helvetica",
        "DejaVu Sans",
    ],
    text="#2B2F33",
    muted_text="#5B6570",
    grid="#E7EAF0",
    axis="#B8C0CC",
    colors=["#2F5D8C", "#7895B2", "#A7BBCD", "#D7E3EE", "#5E748D", "#94A3B8"],
    accent="#B85C38",
    title_size=18,
    label_size=13,
    tick_size=11,
    legend_size=11,
    value_label_size=12,
)


def get_theme(name: str | None = None) -> Theme:
    if name in (None, "", "consulting"):
        return CONSULTING
    raise ValueError(f"Unsupported theme: {name}")


def apply_theme(theme: Theme) -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "savefig.bbox": None,
            "font.family": "sans-serif",
            "font.sans-serif": theme.fonts,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "axes.edgecolor": theme.axis,
            "axes.labelcolor": theme.text,
            "xtick.color": theme.muted_text,
            "ytick.color": theme.muted_text,
            "text.color": theme.text,
            "axes.titlesize": theme.title_size,
            "axes.titleweight": "semibold",
            "axes.labelsize": theme.label_size,
            "xtick.labelsize": theme.tick_size,
            "ytick.labelsize": theme.tick_size,
            "legend.fontsize": theme.legend_size,
            "axes.unicode_minus": False,
        }
    )
