# all2md

## What it does

all2md converts a folder of mixed source materials into clean, AI-ready Markdown.

It routes documents, PDFs, spreadsheets, slide decks, screenshots, scanned images, audio, and video through available local tools, then preserves the source folder structure in the output. The bundled runner writes Markdown files plus `INDEX.md` and `manifest.json` so another agent can navigate the evidence package, see parser choices, and identify conversion failures.

This is a source-preparation skill, not an analysis skill. Its job is to make messy material usable before research, diligence, strategy, or knowledge-base work begins.

## When to use it

- The user has a folder of mixed files that should become Markdown.
- The source package includes PDFs, Office files, images, audio, video, or nested subfolders.
- The agent can read local files and run installed local converters.
- The user needs traceability from Markdown back to original source paths.
- Downstream analysis should begin from an index and manifest rather than ad hoc file browsing.

Do not use it when the user only needs a single small Markdown edit, when the source files should not be processed, or when perfect OCR/transcription fidelity is required without manual review.

## Example input

```text
Convert this source package into Markdown for analysis. It has PDFs, a deck, screenshots, and one interview recording. Keep the folder structure and tell me which files failed.
```

## Expected output

- Markdown files that mirror the source package structure
- `INDEX.md` with links from converted files back to source-relative paths
- `manifest.json` with source hashes, parser choices, OCR/ASR flags, statuses, errors, and output paths
- A short handoff summary with converted count, failed count, output root, parser choices, and quality caveats
- Optional rerun recommendations for failed or low-quality files
- Local output under `skills/all2md/output/` by default, which is ignored by git

## Safety / boundaries

- Process only files the user is allowed to use.
- Treat converted Markdown as derived private material unless the user explicitly says it is publishable.
- Do not commit conversion outputs, private source packages, transcripts, client documents, local service URLs, tokens, model paths, or account-specific workspace paths.
- Public examples must be synthetic or sanitized.
- OCR and ASR output must be spot-checked before quoting.
- Parser failures should be recorded and reported instead of hidden.
