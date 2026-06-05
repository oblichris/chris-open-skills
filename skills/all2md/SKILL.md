---
name: all2md
description: Convert multimodal source materials into clean Markdown by routing documents, PDFs, images, audio, and video through the best available local tools. Use when the user wants to turn folders or files into AI-ready Markdown, especially mixed Office documents, scanned PDFs, Chinese PDFs, images, audio, or video.
---

# all2md

Use this skill to convert mixed source-material packages into clean, AI-ready Markdown. It is designed for research, consulting, diligence, strategy, and knowledge-work folders where clients or researchers provide many nested subfolders of PDFs, decks, spreadsheets, documents, images, audio, and video.

This is a lightweight routing skill: it does not bundle converter binaries, models, virtual environments, or sample data. It chooses the right local tool for each input, preserves the original folder structure, and writes mapping indexes so later agents can navigate the evidence package.

## Use This Skill For

- converting a folder of mixed source materials into Markdown for downstream analysis
- routing PDFs, Office files, screenshots, scanned images, audio, and video through appropriate local converters
- preserving source-folder structure so an agent can trace every Markdown file back to the original package
- creating `INDEX.md` and `manifest.json` artifacts that make large evidence packs navigable
- preparing research, diligence, consulting, strategy, or knowledge-base materials for AI review
- batch conversion where bounded concurrency matters because some parsers are CPU-, memory-, or model-heavy

This is an agent-native utility skill: it depends on real local files, installed tools, filesystem structure, hashes, and conversion manifests.

## Do Not Route Here

- writing analysis from already-clean Markdown
- manual document cleanup where only one small Markdown file needs editing
- extracting secrets, bypassing document access controls, or processing files the user is not allowed to use
- promising perfect OCR, layout, table, formula, or transcript fidelity without spot checks
- publishing converted private source materials as examples

## Default Workflow

1. Confirm the user has permission to process the source files and identify the source package root.
2. Probe the local conversion environment with `command -v` checks or small import checks only when needed.
3. Use `references/routing-contract.md` to choose parser modes by source type, fidelity need, and runtime budget.
4. Run `scripts/convert_all.py` for folder-level work, keeping default output under this skill's ignored `output/` folder unless the user asks otherwise.
5. Inspect `INDEX.md` first, then `manifest.json`, before analyzing the converted Markdown.
6. Use `references/quality-check.md` to spot-check representative outputs and decide whether to rerun failed or low-quality files with a narrower parser.
7. Hand off a concise conversion summary: converted count, failed count, output root, parser choices, and any evidence gaps.

## Core Rules

- preserve the original folder hierarchy unless the user explicitly asks for a flattened output
- keep one source-to-output mapping per file in `manifest.json`
- treat conversion output as derived private material unless the user says it is safe to share
- record parser choice, source hash, source-relative path, OCR/ASR flags, and errors
- prefer rerunning a bad conversion with a better parser over hand-editing evidence Markdown
- keep heavy PDF/OCR/ASR concurrency low by default
- use environment variables for local services and never hard-code private hosts, tokens, model paths, or account-specific locations

## Output Contract

- produce Markdown files that mirror the source package structure
- produce `INDEX.md` for human navigation
- produce `manifest.json` for machine-readable traceability
- include YAML front matter in each durable Markdown output when the runner is used
- include failures instead of hiding them; a failed conversion is an evidence gap
- summarize quality checks and parser fallbacks before downstream analysis starts

## Runtime Assumptions

Prefer an existing local conversion environment if present:

```bash
source "${ALL2MD_ENV:-$HOME/ai-convert-env}/bin/activate"
```

Expected tools may include Docling, Tesseract OCR, pypdf, MarkItDown, OpenDataLoader PDF, MinerU, Marker, a local Whisper HTTP service, faster-whisper, WhisperX, OCRmyPDF, Pandoc, and FFmpeg. If a required tool is missing, check with `command -v <tool>` or a small import probe, then either choose an available fallback or tell the user exactly what is missing.

## Routing

Choose the narrowest reliable path:

| Source | Preferred path |
|---|---|
| DOCX, PPTX, XLSX, HTML, ordinary PDFs | Docling |
| PNG, JPG, JPEG screenshots or scanned images | Docling OCR, then Tesseract OCR fallback |
| Quick PDF, PPTX, Office, web page, or YouTube conversion | MarkItDown |
| PDF needing Markdown plus JSON, layout metadata, images, or tagged PDF | OpenDataLoader PDF |
| Large PDFs at or above 50 MB | pypdf-lite first, then PDF-specific fallbacks |
| Scanned PDF | OCRmyPDF, then Docling |
| Complex Chinese PDF, formulas, dense tables | MinerU or Marker |
| Audio | Local Whisper HTTP service, then faster-whisper fallback |
| Audio needing word timestamps or speaker separation | WhisperX |
| Video | FFmpeg extract audio, then local Whisper HTTP service |
| Final Markdown cleanup | Pandoc to GitHub Flavored Markdown |

For a quick one-off on simple files, use Docling first. For poor PDF output, retry with the PDF-specific fallback instead of manually patching broken Markdown. For large PDFs, avoid starting with Docling unless the user explicitly asks for high-layout fidelity and accepts the runtime cost.

## Batch Concurrency

For folder-level jobs, prefer the bundled concurrent runner:

```bash
python scripts/convert_all.py input_dir --workers 4 --pdf-workers 2 --heavy-workers 1 --asr-workers 1
```

The script scans supported files recursively, routes each file by extension, converts files concurrently, preserves the original source-folder hierarchy, adds YAML front matter, optionally normalizes with Pandoc, and writes two mapping artifacts:

- `INDEX.md`: human-readable conversion map for research and consulting review
- `manifest.json`: machine-readable mapping with source hashes, output paths, parser choice, status, and errors

By default, outputs are written inside this skill at `output/<timestamp>-<source>/`. This keeps conversions from local files or external folders in one traceable place. Use `-o/--output-dir` only when the user explicitly wants a different destination.

By default, an input folder such as `ClientResearchPack/01 interviews/call.mp3` becomes `output/<timestamp>-ClientResearchPack/ClientResearchPack/01 interviews/call.md`. Use `--no-include-root` only when the output should omit the top-level package folder.

Concurrency limits are intentionally split:

| Flag | Default | Use |
|---|---:|---|
| `--workers` | 4 | Light Docling, MarkItDown, and Pandoc work |
| `--pdf-workers` | 2 | PDF, OCR, and OpenDataLoader PDF jobs |
| `--heavy-workers` | 1 | Marker and MinerU jobs |
| `--asr-workers` | 1 | FFmpeg extraction and local Whisper transcription |

Increase light workers for many small Office files. Keep heavy and ASR workers low unless the machine has enough CPU, memory, and model capacity.

In `--pdf-mode auto`, PDFs at or above `--large-pdf-mb 50` skip Docling and try `pypdf-lite` first. This prevents large, image-heavy reports from blocking the whole batch. Use `--pdf-mode docling` only when layout fidelity matters more than runtime.

Useful variants:

```bash
# Fast PPTX/Office-heavy batch
python scripts/convert_all.py input_dir --doc-mode markitdown --workers 6

# PDF batch with OpenDataLoader PDF preferred
python scripts/convert_all.py input_dir --pdf-mode opendataloader-pdf --pdf-workers 2

# Large PDF batch with a higher threshold
python scripts/convert_all.py input_dir --large-pdf-mb 100 --pdf-workers 2

# Scanned PDF batch
python scripts/convert_all.py input_dir --force-ocr --pdf-workers 2

# Image OCR batch
python scripts/convert_all.py image_folder --image-mode auto --workers 4

# Audio/video batch through local Whisper
python scripts/convert_all.py input_dir --asr-mode local-whisper --whisper-url http://127.0.0.1:9000/v1/audio/transcriptions --whisper-noproxy "*" --asr-workers 1

# Multiple source packages, each kept under its own root folder
python scripts/convert_all.py client_pack collected_sources

# Override the default skill-local output only when needed
python scripts/convert_all.py input_dir -o /tmp/all2md-output
```

For large research projects, read the run folder's `INDEX.md` first, then inspect `manifest.json` for failures and parser choices before analyzing the converted Markdown.

## PDF And PPT Alternatives

Use MarkItDown when speed and broad format coverage matter more than layout fidelity:

```bash
markitdown input.pdf -o output.md
markitdown deck.pptx -o deck.md
```

Use OpenDataLoader PDF when PDF output needs structured artifacts beyond plain Markdown, such as JSON, external images, layout-aware extraction, page selection, or tagged PDFs:

```bash
opendataloader-pdf input.pdf --format markdown,json --output-dir out/pdf
```

For PPTX, prefer Docling or MarkItDown. If slide visuals, speaker notes, or image-heavy decks matter, inspect the converted Markdown against the original deck before trusting it.

For large PDFs, use this order unless the user asks otherwise:

1. `pypdf-lite` for fast selectable-text extraction.
2. OpenDataLoader PDF when structured PDF artifacts are available.
3. MarkItDown for broad lightweight conversion.
4. Marker or MinerU for complex Chinese layouts, formulas, or tables.
5. Docling only when layout fidelity is worth the extra time.

`pypdf-lite` is intentionally text-first: it is fast and good for long reports with embedded text, but it will not recover text from scanned pages.

## Image OCR

PNG, JPG, and JPEG files should be treated as OCR inputs, not ordinary documents.

Default route:

```bash
python scripts/convert_all.py screenshots_or_scans --image-mode auto
```

The script tries Docling first because it can preserve more document structure when the image resembles a page or slide. If Docling fails or extracts too little text, it falls back to Tesseract:

```bash
tesseract input.png stdout -l chi_sim+eng
```

Use Tesseract directly when the image is a clean screenshot, scanned page, receipt, form, or simple chart label capture. Use Docling first when the image is a full page with headings, paragraphs, tables, or mixed layout. If the task requires understanding non-text visual content, such as diagrams, charts, UI screenshots, or photos, OCR alone is not enough; use a vision-capable model to describe the image and save that description as Markdown alongside the OCR text.

Always spot-check OCR output. OCR can confuse visually similar characters such as `AI`/`Al`, `OCR`/`COR`, `0`/`O`, and Chinese punctuation, especially in screenshots, compressed JPEGs, and small fonts.

## Document Conversion

Use Docling for ordinary document batches and structured image OCR:

```python
from pathlib import Path
from docling.document_converter import DocumentConverter

input_dir = Path("input")
output_dir = Path("out/md")
converter = DocumentConverter()

for path in input_dir.rglob("*"):
    if path.suffix.lower() not in {".pdf", ".docx", ".pptx", ".xlsx", ".html", ".png", ".jpg", ".jpeg"}:
        continue
    result = converter.convert(str(path))
    out = output_dir / f"{path.stem}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(result.document.export_to_markdown(), encoding="utf-8")
    print(f"converted {path}")
```

## PDF Fallbacks

For scanned PDFs, add a text layer before conversion:

```bash
ocrmypdf input.pdf input_ocr.pdf
```

For complex Chinese PDFs, formulas, and dense layouts:

```bash
mineru -p input.pdf -o out/mineru
marker_single input.pdf out/marker --langs Chinese,English
```

Use the better Markdown output as the final source. Do not merge competing outputs blindly; compare headings, table completeness, formula preservation, and page order first.

## Audio And Video

Extract audio from video before transcription:

```bash
ffmpeg -i input.mp4 -q:a 0 -map a audio.mp3
```

Use the local Whisper HTTP service for daily transcription. The runner expects an OpenAI-compatible transcription endpoint by default:

```bash
export ALL2MD_WHISPER_URL="http://127.0.0.1:9000/v1/audio/transcriptions"
export ALL2MD_WHISPER_NOPROXY="*"
python scripts/convert_all.py media_folder --asr-mode local-whisper --asr-workers 1
```

Override the endpoint per run if the local service uses a different port:

```bash
python scripts/convert_all.py media_folder --whisper-url http://127.0.0.1:8080/v1/audio/transcriptions --whisper-noproxy "*"
```

The request is sent as multipart form data with `file`, `model`, `language`, and `response_format=json`. The response should contain either a top-level `text` field or a `segments` list. In `--asr-mode auto`, the runner tries `local-whisper` first, then falls back to faster-whisper and WhisperX if the local endpoint is unavailable.

For private LAN or Tailscale HTTP endpoints, keep `--whisper-noproxy "*"` so local proxy settings do not intercept the request. Configure private server URLs with `ALL2MD_WHISPER_URL`; do not hardcode private IP addresses, ports, hostnames, or model paths in the published skill.

Use WhisperX only when word-level timestamps, alignment, or speaker separation is required:

```bash
whisperx audio.mp3 --model medium --language zh --output_dir out/whisperx
```

WhisperX speaker diarization may require a Hugging Face token. Ask the user to configure it only when diarization is truly needed.

## Private ASR Client Workspace

Some users may maintain a separate local transcription client workspace. Keep these rules in mind, but keep private deployment values out of the public skill:

- The workspace path should be treated as a local user setting, for example `<local-whisper-client-workspace>`.
- Keep the workspace minimal:
  - `AGENTS.md`: project collaboration instructions
  - `README-whisper-batch.md`: local usage instructions
  - `batch_whisper_client.py`: batch upload/transcription client
  - `output/`: the only place for transcription results
- Do not create `outputs/`, `work/`, or other temporary result directories.
- Do not put server-side files in the client workspace.
- Every transcription must use `batch_whisper_client.py`.
- Results must go under the workspace root `output/`.
- If no output name is specified, create a timestamped batch folder such as `output/YYYYMMDD-HHMMSS-audio-folder/`.
- If `--output xxx` is specified, interpret it only as `output/xxx/`, never as an arbitrary external path.
- Do not place transcription results in Downloads, Desktop, the current directory root, or other ad hoc locations.
- Do not permanently save audio, video, or transcription results on the remote Whisper server unless the user explicitly asks.
- For private network HTTP requests, use `curl --noproxy "*"` or the equivalent client option.
- After editing the client, run `python3 -m py_compile batch_whisper_client.py`.
- Check private service availability with redacted commands such as:

```bash
tailscale ping -c 5 <private-whisper-host>
curl --noproxy "*" <private-whisper-server-url>/health
```

Private deployment details such as Tailscale IP, port, server URL, health URL, model path, and verification notes belong in local private notes or environment variables, not in the GitHub-published skill.

## Normalize Output

Normalize final Markdown with Pandoc when available:

```bash
pandoc input.md -t gfm -o output.md
```

For batches:

```bash
mkdir -p normalized
for f in out/md/*.md; do
  pandoc "$f" -t gfm -o "normalized/$(basename "$f")"
done
```

## Output Standard

When creating durable Markdown files, add concise YAML front matter:

```yaml
---
title: "Source title"
source_path: "original/path.ext"
source_root: "original/package/root"
source_relative_path: "subfolder/original/path.ext"
source_sha256: "optional-hash"
parser: "docling"
parser_version: "x.x.x"
lang: "zh"
page_count: null
ocr_used: false
asr_used: false
created_at: "YYYY-MM-DD"
---
```

Keep extracted images as referenced files instead of base64 blobs. Preserve formulas as LaTeX whenever possible. Keep timestamps in transcripts when they help review or citation.

## Quality Check

Before handing off results, inspect at least one representative output per source type:

- Headings and page order are intact.
- Tables are readable and not flattened into unusable text.
- Scanned PDFs actually contain OCR text.
- Audio/video transcripts include timestamps and do not show obvious language mismatch.
- Output paths mirror the original package structure.
- `INDEX.md` links every converted Markdown file back to its source-relative path.
- `manifest.json` records failures, hashes, parser choices, and source/output mappings.
