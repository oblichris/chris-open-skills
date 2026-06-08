# Output And Style Contract

`agent-chart` produces static artifacts that can be dropped into slides or reports. The default output set is an SVG for editable/vector use, a PNG for quick insertion, and a saved JSON spec for auditability.

Every generation run must write to a fresh timestamped folder below the selected output directory:

```text
output/YYYYMMDD_HHMMSS/
  chart_name.svg
  chart_name.png
  chart_name.spec.json
```

If a timestamp already exists, append a numeric suffix such as `_01`. Do not write generated charts directly into the repository root, directly into `output/`, or next to the source data. Public examples may include input data and specs, but generated output folders should stay out of version control unless they are intentionally sanitized example artifacts.

Naming rules:

- Prefer an explicit English output stem from the user, such as `revenue_bar`.
- If no output name is provided, derive a safe lowercase file stem from the title or chart type.
- Keep the same stem across `.svg`, `.png`, and `.spec.json`.

Style rules:

- Use a white background suitable for business slides.
- Favor a restrained consulting palette with a small set of blues, grays, and accents rather than rainbow colors.
- Use subtle gridlines for cartesian charts.
- Avoid decorative shadows, gradients, and chartjunk.
- Place titles clearly and keep labels readable.
- For grouped, stacked, combo, and colored scatter charts, include a legend when more than one series or category appears.

The default figure should be 16:9 so the PNG lands cleanly in slide workflows. SVG is the safer format when downstream editing is expected, while PNG is convenient for quick insertion into documents or decks.

Agent reporting contract:

- Mention the output directory.
- List generated files.
- Mention the chart type and fields rendered.
- Include validation notes and warnings.
- Do not claim visual or data correctness if the command failed or validation did not run.

This skill deliberately stops before PowerPoint automation. It creates chart assets, not a finished deck layout. If the user asks for slide composition, hand the generated image assets to a presentation workflow after the chart validation has passed.
