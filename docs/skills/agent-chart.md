# agent-chart

## What it does

`agent-chart` turns local CSV, Excel, or pasted CSV-like data into static consulting-style charts. It renders PNG and SVG files through local Python, saves the chart spec next to the image files, and prints a validation summary before accepting the output.

The useful distinction is that the agent may parse the request, but Python validates and renders. That keeps chart generation auditable: fields must exist, numeric values must pass conversion, percent handling is recorded, and output files land in a timestamped folder.

## When to use it

Use this skill when a user asks for PPT-ready or report-ready charts from local data, especially if they name chart fields such as `x=年份,y=收入`, `label=品牌,value=市场份额`, or `bar_y=收入,line_y=利润率`.

It works best for:

- bar, horizontal bar, grouped bar, and stacked bar charts
- line charts
- pie and donut charts
- combo bar-line charts
- scatter charts with optional category coloring
- business-analysis chart assets where a saved `.spec.json` is useful for review

Do not use it for dashboards, maps, Sankey diagrams, interactive charts, automatic insights, or full PowerPoint deck composition.

## Example input

Prompt-driven example:

```text
用 skills/agent-chart/examples/revenue.csv 生成柱状图，x=年份，y=收入，标题=公司收入增长趋势，输出名=revenue_bar
```

Equivalent command:

```bash
python3 skills/agent-chart/scripts/agent_chart_cli.py \
  --input skills/agent-chart/examples/revenue.csv \
  --prompt "生成柱状图，x=年份，y=收入，标题=公司收入增长趋势" \
  --output revenue_bar \
  --format svg,png \
  --output-dir skills/agent-chart/output
```

Spec-driven example:

```bash
python3 skills/agent-chart/scripts/agent_chart_cli.py \
  --input skills/agent-chart/examples/revenue.csv \
  --spec skills/agent-chart/examples/specs/revenue_bar.spec.json \
  --output-dir skills/agent-chart/output
```

## Expected output

The skill produces one timestamped run folder:

```text
skills/agent-chart/output/YYYYMMDD_HHMMSS/
  revenue_bar.svg
  revenue_bar.png
  revenue_bar.spec.json
```

The agent should report the chart type, selected fields, validation result, data notes, output directory, and generated files. A successful run should include a validation summary similar to:

```text
数据校验通过：
- x 字段：年份，5 个唯一值
- y 字段：收入，数值型
- 数据行数：5
- 缺失值：0
- 输出格式：svg, png
```

## Safety / boundaries

The skill does not mutate source data. Generated files are written under `output/YYYYMMDD_HHMMSS/`, and public generated output should remain out of version control unless intentionally sanitized.

Examples in this repository are synthetic. Do not publish raw client data, private reports, resumes, trackers, service URLs, tokens, browser paths, or local absolute paths. If the prompt is ambiguous and the dataset contains several plausible numeric fields, ask the user for explicit field assignments instead of guessing.
