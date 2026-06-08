# Synthetic Business Chart Example

This example proves the `agent-chart` workflow with fictional business data. It uses small CSV files under `skills/agent-chart/examples/` and explicit specs under `skills/agent-chart/examples/specs/`. The data is synthetic: invented revenue, market share, and company metrics for testing chart behavior.

## Input

The example package includes:

- `../revenue.csv`: yearly revenue and profit-margin data.
- `../business_revenue.csv`: yearly revenue split across three fictional business lines.
- `../market_share.csv`: fictional brand share data that sums to 100.
- `../company_scatter.csv`: fictional company revenue, profit, and industry categories.
- `../specs/revenue_bar.spec.json`: explicit bar-chart spec.
- `../specs/business_revenue_grouped_bar.spec.json`: explicit grouped-bar spec.

## Run

From the repository root:

```bash
python3 skills/agent-chart/scripts/agent_chart_cli.py \
  --input skills/agent-chart/examples/revenue.csv \
  --prompt "生成柱状图，x=年份，y=收入，标题=公司收入增长趋势" \
  --output revenue_bar \
  --format svg,png \
  --output-dir skills/agent-chart/output
```

Spec-driven run:

```bash
python3 skills/agent-chart/scripts/agent_chart_cli.py \
  --input skills/agent-chart/examples/business_revenue.csv \
  --spec skills/agent-chart/examples/specs/business_revenue_grouped_bar.spec.json \
  --output-dir skills/agent-chart/output
```

Pasted-data run:

```bash
python3 skills/agent-chart/scripts/agent_chart_cli.py \
  --data "年份,收入\n2021,100\n2022,130\n2023,160" \
  --prompt "生成柱状图，x=年份，y=收入，标题=粘贴数据收入趋势" \
  --output pasted_revenue_bar \
  --format svg,png \
  --output-dir skills/agent-chart/output
```

## Expected Output

Each render creates a timestamped output folder such as:

```text
skills/agent-chart/output/20260608_153000/
  revenue_bar.svg
  revenue_bar.png
  revenue_bar.spec.json
```

The command should print a validation summary before listing files. For the revenue example, the summary should identify `年份` as the x field, `收入` as numeric, report five data rows, and show `svg, png` as output formats. For combo charts using `利润率`, validation should record percent-string conversion in the saved spec.

## Why It Proves The Workflow

This synthetic example exercises the main contract: explicit prompt parsing, field validation, numeric conversion, timestamped output, and saved specs. It also covers both prompt-driven and spec-driven rendering. Because the example data is fictional and tiny, it is safe to publish and easy for a stranger to rerun without private context.
