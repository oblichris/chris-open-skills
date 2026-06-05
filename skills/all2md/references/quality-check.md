# all2md Quality Check

Conversion output is evidence, not decoration. Before using the Markdown for research or analysis, inspect representative outputs and decide whether the conversion is good enough for the downstream decision.

Start with `INDEX.md`. It should show the same package shape as the source folder and link each converted Markdown file to a source-relative path. If the index is missing a major folder, inspect `manifest.json` before assuming the source package was small. Unsupported file types, parser failures, and empty OCR output should be treated as evidence gaps.

For PDFs, check heading order, page order, table readability, footnotes, and formula preservation. A long report with selectable text may be acceptable after `pypdf-lite` even if layout is plain. A scanned PDF is not acceptable unless the output contains real OCR text. A complex PDF with dense tables or bilingual content should be spot-checked against the original pages; if the Markdown collapses tables into unreadable lines, rerun those files with a layout-aware parser.

For Office files, inspect slide titles, speaker notes, table cells, and worksheet names where relevant. Converted decks often lose visual hierarchy. If a deck's argument depends on diagrams or slide composition, note that the Markdown is a text extraction and preserve the original file path for manual review.

For images, look for OCR confusions such as `0` versus `O`, `AI` versus `Al`, broken Chinese punctuation, and missing small text. For audio and video, check language, obvious hallucinated phrases, timestamp usefulness, and whether multiple speakers or poor audio require a more specialized pass.

The handoff summary should include converted count, failed count, output root, parser choices, and the quality caveats that matter. Never describe the converted corpus as complete when `manifest.json` contains failures.
