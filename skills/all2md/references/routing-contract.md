# all2md Routing Contract

The routing contract exists to keep conversion work reproducible. An agent should not treat every source file as a generic document. It should choose the narrowest reliable parser for the file type, the expected content, and the user's tolerance for runtime cost.

Start with the source package shape. Preserve the top-level input folder by default, then mirror subfolders under the output root. This lets later analysis cite `interviews/call-03.md` or `reports/market-study.md` while still tracing the source-relative path in `manifest.json`. Flattening is only appropriate when the user asks for a single working folder and accepts the loss of package structure.

For ordinary Office files and selectable-text PDFs, try Docling first when structure matters. Use MarkItDown when speed and broad format coverage matter more than precise layout. For large PDFs, start with `pypdf-lite` in auto mode because a text-first extraction is often enough for long reports and avoids blocking the batch. Move to OpenDataLoader PDF, Marker, or MinerU only when layout metadata, dense tables, formulas, Chinese PDFs, or page-level artifacts matter.

Treat image files as OCR inputs. Use Docling first for page-like images with headings or tables, then Tesseract for clean screenshots, scanned pages, receipts, and simple forms. OCR is not visual reasoning: if a chart, diagram, UI screenshot, or photo matters beyond visible text, create a separate vision-model description rather than pretending OCR captured it.

Treat video as audio plus metadata unless the user explicitly asks for visual scene analysis. Extract audio with FFmpeg, transcribe through the configured local Whisper-compatible endpoint, and fall back to local faster-whisper or WhisperX when the endpoint is unavailable. Use WhisperX only when timestamps, alignment, or diarization are worth the extra setup.

Concurrency should follow resource class, not just file count. Keep PDF/OCR work bounded, keep ASR and heavy layout models low, and increase light workers only for many small Office or HTML files. When a parser fails, record the failure and continue through the fallback chain. Do not silently drop unsupported files.
