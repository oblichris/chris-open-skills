# agent-chart Skill Test Plan

This file is for testing whether the `agent-chart` skill can produce accurate, polished, consulting-style charts. It should be used after the first implementation is complete.

The test is not only "can it draw a chart"; the goal is to verify:

- Data is interpreted correctly.
- Validation catches field and numeric issues.
- PNG and SVG files are generated.
- The saved `.spec.json` matches the chart request.
- Every run writes into `output/<timestamp>/`.
- The visual result is clean enough for PPT/report use.

## Required Output Folder Rule

Every generation run must create a timestamp-named subfolder under `output/`.

Expected pattern:

```text
output/YYYYMMDD_HHMMSS/
```

Example:

```text
output/20260605_213012/
  revenue_bar.svg
  revenue_bar.png
  revenue_bar.spec.json
```

If one command generates multiple charts, all files from that command should stay in the same timestamped folder.

Do not write chart files directly into the repository root or directly into `output/`.

## Test Data

Create or use these files under `examples/`.

### examples/revenue.csv

```csv
年份,收入,利润率
2021,100,12%
2022,130,14%
2023,160,15%
2024,190,16%
2025,230,18%
```

### examples/market_share.csv

```csv
品牌,市场份额
A品牌,35
B品牌,25
C品牌,20
D品牌,12
其他,8
```

### examples/company_scatter.csv

```csv
公司,收入,利润,行业
公司A,100,12,消费
公司B,130,20,科技
公司C,80,8,制造
公司D,200,35,科技
```

### examples/business_revenue.csv

```csv
年份,业务A,业务B,业务C
2021,80,45,25
2022,95,55,35
2023,120,62,48
2024,145,78,60
2025,170,90,72
```

## Smoke Test Commands

Run these commands from the project root after setup.

### 1. Inspect Revenue Data

```bash
python -m agent_chart.cli --input examples/revenue.csv --inspect
```

Pass criteria:

- Lists `年份`, `收入`, `利润率`.
- Shows `收入` as numeric or safely numeric-like.
- Shows `利润率` as percent-like or convertible.

### 2. Revenue Bar Chart

```bash
python -m agent_chart.cli --input examples/revenue.csv --prompt "生成柱状图，x=年份，y=收入，标题=公司收入增长趋势" --output revenue_bar --format svg,png
```

Expected files:

```text
output/<timestamp>/revenue_bar.svg
output/<timestamp>/revenue_bar.png
output/<timestamp>/revenue_bar.spec.json
```

Pass criteria:

- X axis uses years 2021-2025 in order.
- Y values are 100, 130, 160, 190, 230.
- Title is `公司收入增长趋势`.
- Bars use a restrained consulting-style color.

### 3. Revenue Line Chart

```bash
python -m agent_chart.cli --input examples/revenue.csv --prompt "生成折线图，x=年份，y=收入，标题=公司收入趋势" --output revenue_line --format svg,png
```

Pass criteria:

- Line points match all five revenue values.
- Y-axis gridlines are subtle.
- The line is readable and not visually noisy.

### 4. Revenue Plus Margin Combo Chart

```bash
python -m agent_chart.cli --input examples/revenue.csv --prompt "生成收入和利润率组合图，x=年份，bar_y=收入，line_y=利润率，标题=收入与利润率变化" --output revenue_margin_combo --format svg,png
```

Pass criteria:

- Revenue is rendered as bars.
- Profit margin is rendered as a line.
- Percent values are handled consistently and recorded in the spec or validation notes.
- Secondary y-axis is used when needed.
- Legend clearly distinguishes `收入` and `利润率`.

### 4b. Business Revenue Grouped Bar Chart

```bash
python -m agent_chart.cli --input examples/business_revenue.csv --prompt "生成分组柱状图，x=年份，y=业务A,业务B,业务C，标题=各业务收入变化" --output business_revenue_grouped_bar --format svg,png
```

Pass criteria:

- Each year has three side-by-side bars.
- Legend clearly shows `业务A`, `业务B`, and `业务C`.
- Values match the source data.

### 4c. Business Revenue Stacked Bar Chart

```bash
python -m agent_chart.cli --input examples/business_revenue.csv --prompt "生成堆叠柱状图，x=年份，y=业务A,业务B,业务C，标题=收入结构变化" --output business_revenue_stacked_bar --format svg,png
```

Pass criteria:

- Each year has one stacked bar split into three segments.
- Legend clearly shows `业务A`, `业务B`, and `业务C`.
- Segment values match the source data.

### 5. Market Share Pie Chart

```bash
python -m agent_chart.cli --input examples/market_share.csv --prompt "生成饼图，label=品牌，value=市场份额，标题=市场份额结构" --output market_share_pie --format svg,png
```

Pass criteria:

- Slice values sum to 100.
- Labels are readable.
- Colors are restrained, not rainbow-like.

### 6. Market Share Donut Chart

```bash
python -m agent_chart.cli --input examples/market_share.csv --prompt "生成环形图，label=品牌，value=市场份额，标题=市场份额结构" --output market_share_donut --format svg,png
```

Pass criteria:

- Donut hole is present.
- Segment order and values match source data.
- Labels or legend remain readable.

### 7. Market Share Horizontal Bar Chart

```bash
python -m agent_chart.cli --input examples/market_share.csv --prompt "生成横向条形图，x=市场份额，y=品牌，标题=市场份额排名" --output market_share_horizontal_bar --format svg,png
```

Pass criteria:

- Brand labels are on the category axis.
- Values match 35, 25, 20, 12, 8.
- Chart is easy to scan as a ranking.

### 8. Revenue-Profit Scatter Chart

```bash
python -m agent_chart.cli --input examples/company_scatter.csv --prompt "生成散点图，x=收入，y=利润，标题=收入与利润关系" --output revenue_profit_scatter --format svg,png
```

Pass criteria:

- Each company appears as one point.
- X and Y values match the source data.
- Axis labels are clear.

### 9. Industry-Colored Scatter Chart

```bash
python -m agent_chart.cli --input examples/company_scatter.csv --prompt "生成散点图，x=收入，y=利润，color=行业，标题=收入与利润关系" --output revenue_profit_scatter_by_industry --format svg,png
```

Pass criteria:

- Points are colored by `行业`.
- Legend shows `消费`, `科技`, `制造`.
- Color palette remains professional.

## Direct Spec Test

Create `examples/specs/revenue_bar.spec.json`:

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

Pass criteria:

- The tool renders from the spec without prompt parsing.
- Output files are placed in a fresh timestamped folder.
- Saved spec matches the requested spec plus any validation notes.

## Pasted Data Test

Run:

```bash
python -m agent_chart.cli --data "年份,收入,利润
2021,100,12
2022,130,18
2023,160,25
2024,190,31" --prompt "生成柱状图，x=年份，y=收入，标题=粘贴数据收入趋势" --output pasted_revenue_bar --format svg,png
```

Pass criteria:

- Data is read from `--data`.
- Output is still written under `output/<timestamp>/`.
- Chart values match pasted data.

## Validation Failure Tests

These tests should fail clearly and should not produce misleading charts.

### Missing Field

```bash
python -m agent_chart.cli --input examples/revenue.csv --prompt "生成柱状图，x=年份，y=不存在字段，标题=错误测试" --output should_fail
```

Pass criteria:

- Command fails with a clear missing-field message.
- No chart image is generated.

### Ambiguous Prompt

```bash
python -m agent_chart.cli --input examples/revenue.csv --prompt "生成柱状图，展示趋势" --output should_fail_ambiguous
```

Pass criteria:

- Command asks for explicit fields such as `x=年份,y=收入`.
- No chart image is generated.

## Visual Quality Review Checklist

Open the generated PNG files and score each chart.

Use this scoring:

```text
0 = unacceptable
1 = usable but rough
2 = good enough for internal analysis
3 = good enough for PPT/report
```

Checklist:

- Data accuracy: values, labels, order, and units are correct.
- Layout: no clipped title, labels, legend, or axis text.
- Readability: chart is legible at slide size.
- Style: white background, restrained colors, no shadows, no 3D.
- Font: Microsoft YaHei when installed on the rendering machine; otherwise flag the run as not strict-font compliant.
- Consulting feel: simple, clean, professional, not dashboard-like.
- Chinese rendering: Chinese field names and titles display correctly.
- Export quality: PNG is crisp and SVG opens correctly.
- Output hygiene: every run has its own timestamped folder.

Pass threshold:

- Every chart must score `3` for data accuracy.
- Every chart must score at least `2` for visual quality.
- At least five of the seven chart types should score `3` for PPT/report readiness.

## Final Acceptance

The skill passes this test plan when:

- All smoke test commands run successfully.
- Required failure tests fail safely.
- Every successful command generates PNG, SVG, and `.spec.json`.
- All files are inside `output/<timestamp>/`.
- Charts are visually good enough to paste into a consulting report with little or no manual cleanup.
