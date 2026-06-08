# Chart Spec Contract

`agent-chart` uses an explicit JSON chart spec as the handoff between the agent-facing request and the deterministic Python renderer. The agent may interpret the user prompt, but the renderer should receive a concrete spec whose fields can be validated against the input data.

The contract is intentionally small. A spec should name the chart type, title, required data fields, output name, output formats, theme, and data notes. The renderer may enrich the spec during validation, especially when it coerces percent strings, drops rows with missing required values, or decides whether a combo chart should use a secondary axis.

Common chart spec:

```json
{
  "chart_type": "bar",
  "title": "Company revenue trend",
  "x": "year",
  "y": "revenue",
  "output_name": "revenue_bar",
  "output_formats": ["svg", "png"],
  "theme": "consulting",
  "data_notes": []
}
```

Pie and donut specs use `label` and `value` instead of `x` and `y`:

```json
{
  "chart_type": "donut",
  "title": "Market share mix",
  "label": "brand",
  "value": "share",
  "output_name": "market_share_donut",
  "output_formats": ["svg", "png"],
  "theme": "consulting",
  "data_notes": []
}
```

Combo charts separate the bar and line measures:

```json
{
  "chart_type": "combo_bar_line",
  "title": "Revenue and margin",
  "x": "year",
  "bar_y": "revenue",
  "line_y": "margin",
  "bar_label": "revenue",
  "line_label": "margin",
  "secondary_y": true,
  "output_name": "revenue_margin_combo",
  "output_formats": ["svg", "png"],
  "theme": "consulting",
  "data_notes": []
}
```

Field requirements by chart type:

| chart_type | Required fields |
| --- | --- |
| `bar` | `x`, `y` |
| `horizontal_bar` | `x`, `y`; `x` is numeric and `y` is categorical |
| `grouped_bar` | `x`, multi-field `y` |
| `stacked_bar` | `x`, multi-field `y` |
| `line` | `x`, `y` |
| `pie` | `label`, `value` |
| `donut` | `label`, `value` |
| `combo_bar_line` | `x`, `bar_y`, `line_y` |
| `scatter` | `x`, `y`; optional `size` and `color` |

Agents should prefer explicit field assignments from the user. If the data contains several plausible numeric columns and the prompt only says something like "make a trend chart", stop and ask for fields instead of guessing. The only safe inference is syntactic normalization: for example, `标题=` can map to `title`, and `输出名=` can map to `output_name`.

The saved `.spec.json` is part of the output, not an implementation detail. It should preserve the exact chart type, selected fields, output formats, theme, and validation notes used for rendering. That makes the image auditable and lets another agent rerun or modify the chart without reverse-engineering a bitmap.
