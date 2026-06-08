# agent-chart

`agent-chart` is a local Codex skill and Python CLI for generating clean, consulting-style charts from CSV, Excel, or pasted data.

The most important thing: **tell Codex the chart type and the exact data fields.** The skill will turn your request into a chart spec, validate the data, and render PNG/SVG locally.

## Best Prompt Pattern

Use this structure:

```text
用 <数据文件> 生成 <图表类型>，x=<字段>，y=<字段或多个字段>，标题=<图表标题>，输出名=<英文文件名>
```

For structure charts:

```text
用 <数据文件> 生成 饼图/环形图，label=<分类字段>，value=<数值字段>，标题=<图表标题>，输出名=<英文文件名>
```

For combo charts:

```text
用 <数据文件> 生成组合图，x=<字段>，bar_y=<柱状图指标>，line_y=<折线图指标>，标题=<图表标题>，输出名=<英文文件名>
```

For scatter charts:

```text
用 <数据文件> 生成散点图，x=<横轴数值字段>，y=<纵轴数值字段>，color=<分类字段>，标题=<图表标题>，输出名=<英文文件名>
```

Explicit field names are much safer than vague prompts like “帮我画个趋势图”. If a file has multiple numeric columns, write `x=...` and `y=...` clearly.

## Prompt Cookbook

### 1. 柱状图

```text
用 examples/revenue.csv 生成柱状图，x=年份，y=收入，标题=公司收入增长趋势，输出名=revenue_bar
```

CLI form:

```bash
python -m agent_chart.cli --input examples/revenue.csv --prompt "生成柱状图，x=年份，y=收入，标题=公司收入增长趋势" --output revenue_bar --format svg,png
```

### 2. 折线图

```text
用 examples/revenue.csv 生成折线图，x=年份，y=收入，标题=公司收入趋势，输出名=revenue_line
```

CLI form:

```bash
python -m agent_chart.cli --input examples/revenue.csv --prompt "生成折线图，x=年份，y=收入，标题=公司收入趋势" --output revenue_line --format svg,png
```

### 3. 横向条形图

```text
用 examples/market_share.csv 生成横向条形图，x=市场份额，y=品牌，标题=市场份额排名，输出名=market_share_rank
```

CLI form:

```bash
python -m agent_chart.cli --input examples/market_share.csv --prompt "生成横向条形图，x=市场份额，y=品牌，标题=市场份额排名" --output market_share_rank --format svg,png
```

### 4. 分组柱状图

每个年份下面并排几根柱子，适合对比多个业务、区域、产品线。

```text
用 examples/business_revenue.csv 生成分组柱状图，x=年份，y=业务A,业务B,业务C，标题=各业务收入变化，输出名=business_revenue_grouped
```

CLI form:

```bash
python -m agent_chart.cli --input examples/business_revenue.csv --prompt "生成分组柱状图，x=年份，y=业务A,业务B,业务C，标题=各业务收入变化" --output business_revenue_grouped --format svg,png
```

### 5. 堆叠柱状图

每个年份一根柱子，柱子内部拆成几段，适合看结构变化。

```text
用 examples/business_revenue.csv 生成堆叠柱状图，x=年份，y=业务A,业务B,业务C，标题=收入结构变化，输出名=business_revenue_stacked
```

CLI form:

```bash
python -m agent_chart.cli --input examples/business_revenue.csv --prompt "生成堆叠柱状图，x=年份，y=业务A,业务B,业务C，标题=收入结构变化" --output business_revenue_stacked --format svg,png
```

### 6. 饼图

```text
用 examples/market_share.csv 生成饼图，label=品牌，value=市场份额，标题=市场份额结构，输出名=market_share_pie
```

CLI form:

```bash
python -m agent_chart.cli --input examples/market_share.csv --prompt "生成饼图，label=品牌，value=市场份额，标题=市场份额结构" --output market_share_pie --format svg,png
```

### 7. 环形图

```text
用 examples/market_share.csv 生成环形图，label=品牌，value=市场份额，标题=市场份额结构，输出名=market_share_donut
```

CLI form:

```bash
python -m agent_chart.cli --input examples/market_share.csv --prompt "生成环形图，label=品牌，value=市场份额，标题=市场份额结构" --output market_share_donut --format svg,png
```

### 8. 组合图

柱状图 + 折线图，适合“规模 + 比率”。

```text
用 examples/revenue.csv 生成组合图，x=年份，bar_y=收入，line_y=利润率，标题=收入与利润率变化，输出名=revenue_margin_combo
```

CLI form:

```bash
python -m agent_chart.cli --input examples/revenue.csv --prompt "生成组合图，x=年份，bar_y=收入，line_y=利润率，标题=收入与利润率变化" --output revenue_margin_combo --format svg,png
```

### 9. 散点图

```text
用 examples/company_scatter.csv 生成散点图，x=收入，y=利润，标题=收入与利润关系，输出名=revenue_profit_scatter
```

CLI form:

```bash
python -m agent_chart.cli --input examples/company_scatter.csv --prompt "生成散点图，x=收入，y=利润，标题=收入与利润关系" --output revenue_profit_scatter --format svg,png
```

### 10. 按分类着色的散点图

```text
用 examples/company_scatter.csv 生成散点图，x=收入，y=利润，color=行业，标题=收入与利润关系，输出名=revenue_profit_by_industry
```

CLI form:

```bash
python -m agent_chart.cli --input examples/company_scatter.csv --prompt "生成散点图，x=收入，y=利润，color=行业，标题=收入与利润关系" --output revenue_profit_by_industry --format svg,png
```

## Pasted Data Prompt

You can paste data directly:

```text
用下面的数据生成分组柱状图，x=年份，y=业务A,业务B,业务C，标题=各业务收入变化，输出名=business_grouped

年份,业务A,业务B,业务C
2021,80,45,25
2022,95,55,35
2023,120,62,48
2024,145,78,60
2025,170,90,72
```

CLI form:

```bash
python -m agent_chart.cli --data "年份,业务A,业务B,业务C
2021,80,45,25
2022,95,55,35
2023,120,62,48
2024,145,78,60
2025,170,90,72" --prompt "生成分组柱状图，x=年份，y=业务A,业务B,业务C，标题=各业务收入变化" --output business_grouped --format svg,png
```

## Field Cheat Sheet

- `x`: horizontal axis or primary grouping field, such as `年份`.
- `y`: numeric value field. For grouped/stacked bars, use multiple fields: `y=业务A,业务B,业务C`.
- `label`: category label for pie/donut charts.
- `value`: numeric value for pie/donut charts.
- `bar_y`: bar metric in a combo chart.
- `line_y`: line metric in a combo chart.
- `color`: category field for colored scatter charts.
- `标题`: chart title.
- `输出名` / `--output`: output file stem.

## Supported Chart Types

| 中文说法 | chart_type | Required fields |
| --- | --- | --- |
| 柱状图 | `bar` | `x`, `y` |
| 横向条形图 | `horizontal_bar` | `x`, `y` |
| 分组柱状图 / 簇状柱状图 | `grouped_bar` | `x`, multi-field `y` |
| 堆叠柱状图 / 堆积柱状图 | `stacked_bar` | `x`, multi-field `y` |
| 折线图 | `line` | `x`, `y` |
| 饼图 | `pie` | `label`, `value` |
| 环形图 | `donut` | `label`, `value` |
| 组合图 | `combo_bar_line` | `x`, `bar_y`, `line_y` |
| 散点图 | `scatter` | `x`, `y`, optional `color` |

## Output Rule

Every render creates a fresh timestamped folder:

```text
output/YYYYMMDD_HHMMSS/
  chart_name.svg
  chart_name.png
  chart_name.spec.json
```

Charts are never written directly to the repository root or directly to `output/`.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

You can run either:

```bash
agent-chart --input examples/revenue.csv --inspect
```

or:

```bash
python -m agent_chart.cli --input examples/revenue.csv --inspect
```

## Chart Spec

You can skip prompt parsing and render directly from JSON:

```json
{
  "chart_type": "bar",
  "title": "公司收入增长趋势",
  "x": "年份",
  "y": "收入",
  "output_name": "revenue_bar_from_spec",
  "output_formats": ["svg", "png"],
  "theme": "consulting",
  "data_notes": []
}
```

Run:

```bash
python -m agent_chart.cli --input examples/revenue.csv --spec examples/specs/revenue_bar.spec.json
```

## Validation

Before rendering, the CLI checks:

- Referenced fields exist.
- Numeric fields are numeric or safely convertible.
- Percent strings like `12%` are converted to numeric percentage points and recorded in the saved spec.
- Missing values in required fields are reported and dropped.
- Pie/donut totals are reported.
- Combo charts use a secondary y-axis when scales differ.

## Style

- White background.
- 16:9 PNG output at `1200x675`.
- Microsoft YaHei is the first configured font. If the machine does not have Microsoft YaHei installed, Matplotlib falls back to the next available Chinese-capable font for PNG rendering.
- Restrained consulting palette with blue/gray main colors and one accent color.

## Limits

V1 intentionally does not support dashboards, maps, Sankey charts, interactive charts, automatic insights, or PowerPoint layout automation.
