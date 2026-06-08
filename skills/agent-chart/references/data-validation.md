# Data Validation Protocol

`agent-chart` treats chart rendering as the final step after data validation. The renderer must not silently draw from bad fields, ambiguous fields, or unreported coercions. The validation summary is part of the user-facing answer because the user needs to know what data was actually charted.

Validation starts with source loading. The tool accepts CSV, Excel, or pasted CSV-like text. The source file is never mutated; validation works on an in-memory copy. If a file path is missing, an extension is unsupported, or a selected Excel sheet cannot be loaded, fail before creating any chart output.

Field validation rules:

- Every referenced field must exist exactly as named in the loaded dataframe.
- If no chart fields were specified, fail and ask for explicit assignments such as `x=year,y=revenue`.
- For grouped and stacked bars, `y` must resolve to multiple numeric fields.
- For pie and donut charts, `label` should be categorical and `value` must be numeric or safely convertible.
- For scatter charts, `x`, `y`, and optional `size` must be numeric or safely convertible; `color` is categorical.

Numeric validation rules:

- Native integer and float columns pass without conversion.
- Numeric-looking strings can be converted after stripping thousands separators.
- Percent strings such as `12%` are converted to numeric percentage points, for example `12% -> 12`.
- Any conversion decision must be appended to `data_notes` and printed in the validation summary.
- If all values in a required numeric field fail conversion, stop with a clear error.

Missing-value rules:

- Count missing values across required chart fields before dropping rows.
- Drop rows only when the affected fields are required and enough valid rows remain.
- If all rows would be removed, fail rather than rendering an empty or misleading chart.
- Include the dropped-row count in the validation summary.

Chart-specific checks:

- Pie and donut charts should print the `value` total. If the total looks percentage-like but is materially different from 100, warn the user.
- Combo charts should compare the magnitude of `bar_y` and `line_y`. When the measures have very different scales, use a secondary axis and report that decision.
- Horizontal bars should treat `x` as numeric and `y` as the category label.

Minimum validation summary:

```text
Data validation passed:
- x field: year, 5 unique values
- y field: revenue, numeric
- row count: 5
- missing values: 0
- output formats: svg, png
```

If validation emits warnings, the agent should include them when reporting the output. A chart image without the validation context is not considered complete for this skill.
