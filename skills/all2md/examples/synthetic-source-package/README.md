# Synthetic Source Package Example

This example describes a fictional conversion run for a small diligence folder. It does not include real client files, private paths, transcripts, or converted source material.

## Input

```text
synthetic-source-package/
├── brief.docx
├── market-report.pdf
├── screenshots/
│   └── pricing-page.png
└── interviews/
    └── founder-call.mp3
```

The user asks:

```text
Convert this mixed source package into Markdown so another agent can review the evidence. Keep the original folder structure and tell me what failed.
```

## Run

```bash
python skills/all2md/scripts/convert_all.py synthetic-source-package \
  --workers 4 \
  --pdf-workers 2 \
  --heavy-workers 1 \
  --asr-workers 1 \
  --run-name synthetic-source-package
```

## Expected output shape

```text
skills/all2md/output/<timestamp>-synthetic-source-package/
├── INDEX.md
├── manifest.json
└── synthetic-source-package/
    ├── brief.md
    ├── market-report.md
    ├── screenshots/
    │   └── pricing-page.md
    └── interviews/
        └── founder-call.md
```

`INDEX.md` gives the human map from converted Markdown back to source-relative paths. `manifest.json` records source hashes, parser choices, OCR/ASR flags, durations, output paths, and failures.

## Example handoff

The agent should report something like:

```text
Converted 4 of 4 supported files into skills/all2md/output/<timestamp>-synthetic-source-package.
Parsers used: Docling for brief.docx, pypdf-lite for market-report.pdf, Tesseract OCR for pricing-page.png, local-whisper for founder-call.mp3.
Quality check: the PDF headings and page order look usable; the screenshot OCR needs review around price labels; the transcript is good enough for thematic review but should not be quoted without replaying the audio.
```

The important proof is not the exact Markdown text. It is the traceable conversion package: folder mirroring, index, manifest, parser choices, and a clear statement of quality caveats.
