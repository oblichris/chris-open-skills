---
name: agent-chart
description: Generate clean consulting-style charts from local CSV, Excel, or pasted data. Use when the user asks for bar, horizontal bar, line, pie, donut, combo bar-line, or scatter charts for PPTs, reports, or business analysis, especially when accuracy, PNG/SVG export, and local rendering matter.
---

# agent-chart

Use this skill to generate static, PPT-ready charts from local data through a deterministic Python renderer.

## Use This Skill For

- Turning CSV, Excel, or pasted CSV-like data into clean PNG/SVG charts for slides, reports, and business analysis.
- Requests for `bar`, `horizontal_bar`, `grouped_bar`, `stacked_bar`, `line`, `pie`, `donut`, `combo_bar_line`, or `scatter` charts where the source data is local or pasted by the user.
- Cases where chart accuracy matters: field validation, numeric coercion, percent handling, missing-value reporting, and saved chart specs should all be visible.
- Consulting-style static charts that need a white background, restrained colors, and a reusable `.spec.json` handoff.

## Do Not Route Here

- Do not use this skill for dashboards, maps, Sankey charts, interactive charts, automatic insight generation, or PowerPoint deck layout.
- Do not use it when the user only wants chart advice or a hand-drawn conceptual diagram.
- Do not render from ambiguous prompts when multiple plausible fields exist. Ask for explicit `x=...`, `y=...`, `label=...`, `value=...`, `bar_y=...`, or `line_y=...`.
- Do not mutate source files. The renderer reads data, validates a copy, and writes generated artifacts under `output/`.

## Default Workflow

1. Identify the user's data source: CSV, Excel, or pasted CSV-like data.
2. Prefer explicit fields in the request, such as `x=年份,y=收入` or `label=品牌,value=市场份额`.
3. Inspect unfamiliar data before rendering:

```bash
python -m agent_chart.cli --input skills/agent-chart/examples/revenue.csv --inspect
```

4. Create a chart from either a prompt or an explicit JSON spec.
5. Read the validation summary before accepting the output.
6. Confirm generated files are in `output/YYYYMMDD_HHMMSS/` and include `.svg`, `.png`, and `.spec.json`.

## Core Rules

- The model or prompt parser may choose chart configuration, but local Python must validate data and render the chart.
- Supported output formats in v1 are `svg` and `png`.
- Every render creates a fresh timestamped folder below the selected output directory.
- Field references must exist in the input data before rendering.
- Numeric chart fields must be numeric or safely convertible; percent strings such as `12%` are converted to numeric percentage points and recorded in `data_notes`.
- Missing values in required fields are reported; rows with required missing values are dropped only after the count is surfaced.
- Pie and donut charts report the value total and warn when percentage-like totals are suspicious.
- Save the final chart spec next to the image outputs so the chart can be audited or rerun.

## Output Contract

The agent should report:

- input file or pasted-data source used
- chart type and fields selected
- validation result and any data notes
- generated output directory
- generated filenames

Expected files:

```text
output/YYYYMMDD_HHMMSS/
  chart_name.svg
  chart_name.png
  chart_name.spec.json
```

## Commands

Inspect fields:

```bash
python -m agent_chart.cli --input skills/agent-chart/examples/revenue.csv --inspect
```

Render from prompt:

```bash
python -m agent_chart.cli --input skills/agent-chart/examples/revenue.csv --prompt "生成柱状图，x=年份，y=收入，标题=公司收入增长趋势" --output revenue_bar --format svg,png
```

Render from spec:

```bash
python -m agent_chart.cli --input skills/agent-chart/examples/revenue.csv --spec skills/agent-chart/examples/specs/revenue_bar.spec.json
```

Pasted data:

```bash
python -m agent_chart.cli --data "年份,收入\n2021,100\n2022,130" --prompt "生成柱状图，x=年份，y=收入，标题=收入趋势" --output pasted_revenue_bar
```
