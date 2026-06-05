#!/usr/bin/env python3
"""Batch convert mixed files to Markdown with bounded concurrency.

This script is intentionally dependency-light. It orchestrates local tools such
as Docling, MarkItDown, OpenDataLoader PDF, OCRmyPDF, FFmpeg, faster-whisper,
WhisperX, Pandoc, Marker, and MinerU when they are already installed.
"""

from __future__ import annotations

import argparse
import concurrent.futures
from dataclasses import dataclass
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time


DOC_EXTS = {".docx", ".pptx", ".xlsx", ".html", ".htm"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg"}
PDF_EXTS = {".pdf"}
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".avi"}
SUPPORTED_EXTS = DOC_EXTS | IMAGE_EXTS | PDF_EXTS | AUDIO_EXTS | VIDEO_EXTS


class ConversionError(RuntimeError):
    pass


@dataclass(frozen=True)
class SourceItem:
    path: Path
    root: Path
    output_prefix: Path

    @property
    def relative_path(self) -> Path:
        return self.path.relative_to(self.root)


def build_env() -> tuple[dict[str, str], Path]:
    env = os.environ.copy()
    env_dir = Path(env.get("ALL2MD_ENV", Path.home() / "ai-convert-env")).expanduser()
    bin_dir = env_dir / "bin"
    if bin_dir.exists():
        env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '')}"
    return env, env_dir


ENV, ENV_DIR = build_env()
ENV_PYTHON = ENV_DIR / "bin" / "python"
PYTHON = str(ENV_PYTHON if ENV_PYTHON.exists() else Path(sys.executable))
SKILL_DIR = Path(__file__).resolve().parents[1]


def which(command: str) -> str | None:
    return shutil.which(command, path=ENV.get("PATH"))


def run(cmd: list[str], *, cwd: Path | None = None, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=ENV,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def output_path_for(item: SourceItem, output_root: Path) -> Path:
    return (output_root / item.output_prefix / item.relative_path).with_suffix(".md")


def write_frontmatter(
    output: Path,
    source: Path,
    parser: str,
    *,
    source_root: Path,
    source_relative_path: Path,
    ocr_used: bool,
    asr_used: bool,
) -> None:
    body = output.read_text(encoding="utf-8", errors="replace")
    if body.startswith("---\n"):
        return
    metadata = {
        "title": source.stem,
        "source_path": str(source),
        "source_root": str(source_root),
        "source_relative_path": source_relative_path.as_posix(),
        "source_sha256": sha256(source),
        "parser": parser,
        "parser_version": None,
        "lang": None,
        "page_count": None,
        "ocr_used": ocr_used,
        "asr_used": asr_used,
        "created_at": dt.date.today().isoformat(),
    }
    lines = ["---"]
    for key, value in metadata.items():
        if value is None:
            rendered = "null"
        elif isinstance(value, bool):
            rendered = "true" if value else "false"
        else:
            rendered = json.dumps(value, ensure_ascii=False)
        lines.append(f"{key}: {rendered}")
    lines.extend(["---", "", body])
    output.write_text("\n".join(lines), encoding="utf-8")


def ensure_nonempty_markdown(output: Path, parser: str) -> None:
    if not output.exists():
        raise ConversionError(f"{parser} did not create {output}")
    if output.stat().st_size < 24:
        raise ConversionError(f"{parser} output is too small: {output}")


def ensure_text_density(output: Path, parser: str, min_chars: int) -> None:
    ensure_nonempty_markdown(output, parser)
    text = output.read_text(encoding="utf-8", errors="replace")
    if len(text.strip()) < min_chars:
        raise ConversionError(f"{parser} output has too little extractable text")


def convert_with_docling(source: Path, output: Path) -> str:
    code = r"""
from pathlib import Path
from docling.document_converter import DocumentConverter
import sys
src = Path(sys.argv[1])
dst = Path(sys.argv[2])
dst.parent.mkdir(parents=True, exist_ok=True)
result = DocumentConverter().convert(str(src))
dst.write_text(result.document.export_to_markdown(), encoding="utf-8")
"""
    proc = run([PYTHON, "-c", code, str(source), str(output)])
    if proc.returncode != 0:
        raise ConversionError(proc.stderr.strip() or proc.stdout.strip() or "docling failed")
    ensure_nonempty_markdown(output, "docling")
    return "docling"


def convert_with_pypdf_lite(source: Path, output: Path) -> str:
    code = r"""
from pathlib import Path
from pypdf import PdfReader
import sys
src = Path(sys.argv[1])
dst = Path(sys.argv[2])
reader = PdfReader(str(src))
dst.parent.mkdir(parents=True, exist_ok=True)
parts = [f"# {src.stem}", ""]
for index, page in enumerate(reader.pages, 1):
    text = (page.extract_text() or "").strip()
    parts.append(f"## Page {index}\n")
    parts.append(text if text else "[No extractable text on this page]")
    parts.append("")
dst.write_text("\n".join(parts), encoding="utf-8")
"""
    proc = run([PYTHON, "-c", code, str(source), str(output)])
    if proc.returncode != 0:
        raise ConversionError(proc.stderr.strip() or proc.stdout.strip() or "pypdf-lite failed")
    ensure_text_density(output, "pypdf-lite", min_chars=200)
    return "pypdf-lite"


def convert_with_markitdown(source: Path, output: Path) -> str:
    if not which("markitdown"):
        raise ConversionError("markitdown not found")
    output.parent.mkdir(parents=True, exist_ok=True)
    proc = run(["markitdown", str(source), "-o", str(output)])
    if proc.returncode != 0:
        raise ConversionError(proc.stderr.strip() or proc.stdout.strip() or "markitdown failed")
    ensure_nonempty_markdown(output, "markitdown")
    return "markitdown"


def convert_image_with_tesseract(source: Path, output: Path, language: str) -> str:
    if not which("tesseract"):
        raise ConversionError("tesseract not found")
    langs = "chi_sim+eng" if language.startswith("zh") else language or "eng"
    proc = run(["tesseract", str(source), "stdout", "-l", langs])
    if proc.returncode != 0:
        raise ConversionError(proc.stderr.strip() or proc.stdout.strip() or "tesseract failed")
    text = proc.stdout.strip()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(f"# {source.stem}\n\n{text}\n", encoding="utf-8")
    ensure_text_density(output, "tesseract-ocr", min_chars=12)
    return "tesseract-ocr"


def copy_first_markdown(temp_dir: Path, output: Path, parser: str) -> str:
    candidates = sorted(temp_dir.rglob("*.md"), key=lambda p: p.stat().st_size, reverse=True)
    if not candidates:
        raise ConversionError(f"{parser} did not create a Markdown file")
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(candidates[0], output)
    ensure_nonempty_markdown(output, parser)
    return parser


def convert_with_opendataloader(source: Path, output: Path) -> str:
    if not which("opendataloader-pdf"):
        raise ConversionError("opendataloader-pdf not found")
    with tempfile.TemporaryDirectory(prefix="all2md-opendl-") as tmp:
        temp_dir = Path(tmp)
        proc = run(["opendataloader-pdf", str(source), "--format", "markdown,json", "--output-dir", str(temp_dir)])
        if proc.returncode != 0:
            raise ConversionError(proc.stderr.strip() or proc.stdout.strip() or "opendataloader-pdf failed")
        return copy_first_markdown(temp_dir, output, "opendataloader-pdf")


def convert_with_marker(source: Path, output: Path) -> str:
    if not which("marker_single"):
        raise ConversionError("marker_single not found")
    with tempfile.TemporaryDirectory(prefix="all2md-marker-") as tmp:
        temp_dir = Path(tmp)
        proc = run(["marker_single", str(source), str(temp_dir), "--langs", "Chinese,English"])
        if proc.returncode != 0:
            raise ConversionError(proc.stderr.strip() or proc.stdout.strip() or "marker failed")
        return copy_first_markdown(temp_dir, output, "marker")


def convert_with_mineru(source: Path, output: Path) -> str:
    if not which("mineru"):
        raise ConversionError("mineru not found")
    with tempfile.TemporaryDirectory(prefix="all2md-mineru-") as tmp:
        temp_dir = Path(tmp)
        proc = run(["mineru", "-p", str(source), "-o", str(temp_dir)])
        if proc.returncode != 0:
            raise ConversionError(proc.stderr.strip() or proc.stdout.strip() or "mineru failed")
        return copy_first_markdown(temp_dir, output, "mineru")


def ocr_pdf(source: Path) -> Path:
    if not which("ocrmypdf"):
        raise ConversionError("ocrmypdf not found")
    temp = Path(tempfile.mkdtemp(prefix="all2md-ocr-")) / f"{source.stem}_ocr.pdf"
    proc = run(["ocrmypdf", str(source), str(temp)])
    if proc.returncode != 0:
        raise ConversionError(proc.stderr.strip() or proc.stdout.strip() or "ocrmypdf failed")
    return temp


def extract_audio(source: Path) -> Path:
    if not which("ffmpeg"):
        raise ConversionError("ffmpeg not found")
    temp = Path(tempfile.mkdtemp(prefix="all2md-audio-")) / f"{source.stem}.mp3"
    proc = run(["ffmpeg", "-y", "-i", str(source), "-q:a", "0", "-map", "a", str(temp)])
    if proc.returncode != 0:
        raise ConversionError(proc.stderr.strip() or proc.stdout.strip() or "ffmpeg failed")
    return temp


def transcribe_with_local_whisper(
    source: Path,
    output: Path,
    model: str,
    language: str,
    whisper_url: str,
    whisper_noproxy: str,
) -> str:
    if not which("curl"):
        raise ConversionError("curl not found")
    cmd = [
        "curl",
        "-fsS",
        "-X",
        "POST",
    ]
    if whisper_noproxy:
        cmd.extend(["--noproxy", whisper_noproxy])
    cmd.extend(
        [
            whisper_url,
            "-F",
            f"file=@{source}",
            "-F",
            f"model={model}",
            "-F",
            "response_format=json",
        ]
    )
    if language:
        cmd.extend(["-F", f"language={language}"])
    proc = run(cmd)
    if proc.returncode != 0:
        raise ConversionError(proc.stderr.strip() or proc.stdout.strip() or "local whisper request failed")

    text = ""
    try:
        payload = json.loads(proc.stdout)
        if isinstance(payload, dict):
            if isinstance(payload.get("text"), str):
                text = payload["text"]
            elif isinstance(payload.get("segments"), list):
                chunks = []
                for segment in payload["segments"]:
                    if isinstance(segment, dict):
                        start = segment.get("start")
                        content = segment.get("text", "")
                        if start is not None:
                            chunks.append(f"[{float(start):.1f}s] {content}")
                        else:
                            chunks.append(str(content))
                text = "\n".join(chunks)
        elif isinstance(payload, list):
            text = "\n".join(str(item) for item in payload)
    except json.JSONDecodeError:
        text = proc.stdout

    text = text.strip()
    if not text:
        raise ConversionError("local whisper returned empty transcription")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(f"# {source.stem}\n\n{text}\n", encoding="utf-8")
    ensure_nonempty_markdown(output, "local-whisper")
    return "local-whisper"


def transcribe_with_faster_whisper(source: Path, output: Path, model: str, language: str) -> str:
    code = r"""
from pathlib import Path
from faster_whisper import WhisperModel
import sys
src = Path(sys.argv[1])
dst = Path(sys.argv[2])
model_name = sys.argv[3]
language = sys.argv[4] or None
dst.parent.mkdir(parents=True, exist_ok=True)
model = WhisperModel(model_name, device="cpu")
segments, info = model.transcribe(str(src), language=language)
with dst.open("w", encoding="utf-8") as f:
    for segment in segments:
        f.write(f"[{segment.start:.1f}s] {segment.text}\n")
"""
    proc = run([PYTHON, "-c", code, str(source), str(output), model, language])
    if proc.returncode != 0:
        raise ConversionError(proc.stderr.strip() or proc.stdout.strip() or "faster-whisper failed")
    ensure_nonempty_markdown(output, "faster-whisper")
    return "faster-whisper"


def transcribe_with_whisperx(source: Path, output: Path, model: str, language: str) -> str:
    if not which("whisperx"):
        raise ConversionError("whisperx not found")
    with tempfile.TemporaryDirectory(prefix="all2md-whisperx-") as tmp:
        temp_dir = Path(tmp)
        cmd = ["whisperx", str(source), "--model", model, "--output_dir", str(temp_dir)]
        if language:
            cmd.extend(["--language", language])
        proc = run(cmd)
        if proc.returncode != 0:
            raise ConversionError(proc.stderr.strip() or proc.stdout.strip() or "whisperx failed")
        return copy_first_markdown(temp_dir, output, "whisperx")


def normalize_with_pandoc(output: Path) -> None:
    if not which("pandoc") or not output.exists():
        return
    temp = output.with_suffix(".pandoc.tmp.md")
    proc = run(["pandoc", str(output), "-t", "gfm", "-o", str(temp)])
    if proc.returncode == 0 and temp.exists():
        temp.replace(output)
    elif temp.exists():
        temp.unlink()


def fallback_chain(kind: str, source: Path, args: argparse.Namespace) -> list[str]:
    if kind == "pdf":
        if args.pdf_mode != "auto":
            return [args.pdf_mode]
        if source.stat().st_size >= args.large_pdf_mb * 1024 * 1024:
            return ["pypdf-lite", "opendataloader-pdf", "markitdown", "marker", "mineru"]
        return ["docling", "markitdown", "opendataloader-pdf", "marker", "mineru"]
    if kind == "doc":
        if args.doc_mode != "auto":
            return [args.doc_mode]
        return ["docling", "markitdown"]
    if kind == "image":
        if args.image_mode != "auto":
            return [args.image_mode]
        return ["docling", "tesseract-ocr"]
    if kind == "audio":
        if args.asr_mode == "local-whisper":
            return ["local-whisper"]
        if args.asr_mode == "whisperx":
            return ["whisperx"]
        if args.asr_mode == "faster-whisper":
            return ["faster-whisper"]
        return ["local-whisper", "faster-whisper", "whisperx"]
    raise ConversionError(f"unsupported kind: {kind}")


def classify(source: Path) -> str:
    suffix = source.suffix.lower()
    if suffix in PDF_EXTS:
        return "pdf"
    if suffix in DOC_EXTS:
        return "doc"
    if suffix in IMAGE_EXTS:
        return "image"
    if suffix in AUDIO_EXTS:
        return "audio"
    if suffix in VIDEO_EXTS:
        return "video"
    return "skip"


def convert_by_tool(tool: str, source: Path, output: Path, args: argparse.Namespace) -> str:
    if tool == "docling":
        return convert_with_docling(source, output)
    if tool == "pypdf-lite":
        return convert_with_pypdf_lite(source, output)
    if tool == "markitdown":
        return convert_with_markitdown(source, output)
    if tool == "tesseract-ocr":
        return convert_image_with_tesseract(source, output, args.language)
    if tool == "opendataloader-pdf":
        return convert_with_opendataloader(source, output)
    if tool == "marker":
        return convert_with_marker(source, output)
    if tool == "mineru":
        return convert_with_mineru(source, output)
    if tool == "faster-whisper":
        return transcribe_with_faster_whisper(source, output, args.asr_model, args.language)
    if tool == "local-whisper":
        return transcribe_with_local_whisper(
            source,
            output,
            args.asr_model,
            args.language,
            args.whisper_url,
            args.whisper_noproxy,
        )
    if tool == "whisperx":
        return transcribe_with_whisperx(source, output, args.asr_model, args.language)
    raise ConversionError(f"unknown tool: {tool}")


def semaphore_for(kind: str, tool: str) -> str:
    if tool in {"marker", "mineru"}:
        return "heavy"
    if tool in {"local-whisper", "faster-whisper", "whisperx"}:
        return "asr"
    if tool in {"opendataloader-pdf", "pypdf-lite"} or kind == "pdf":
        return "pdf"
    return "light"


def convert_one(
    item: SourceItem,
    output_root: Path,
    args: argparse.Namespace,
    semaphores: dict[str, threading.Semaphore],
) -> dict[str, object]:
    started = time.time()
    source = item.path.resolve()
    output = output_path_for(item, output_root)
    kind = classify(source)
    record: dict[str, object] = {
        "source_path": str(source),
        "source_root": str(item.root),
        "source_relative_path": item.relative_path.as_posix(),
        "output_path": str(output),
        "output_relative_path": output.relative_to(output_root).as_posix(),
        "source_sha256": sha256(source),
        "kind": kind,
        "status": "failed",
        "parser": None,
        "ocr_used": False,
        "asr_used": False,
        "large_pdf": bool(kind == "pdf" and source.stat().st_size >= args.large_pdf_mb * 1024 * 1024),
        "error": None,
        "duration_seconds": None,
    }

    try:
        work_source = source
        if kind == "video":
            with semaphores["video"]:
                work_source = extract_audio(source)
            kind = "audio"
            record["asr_used"] = True

        if kind == "pdf" and args.force_ocr:
            with semaphores["pdf"]:
                work_source = ocr_pdf(source)
            record["ocr_used"] = True

        if kind in {"pdf", "doc", "image"}:
            chain = fallback_chain(kind, source, args)
            if kind == "image":
                record["ocr_used"] = True
        elif kind == "audio":
            chain = fallback_chain("audio", source, args)
            record["asr_used"] = True
        else:
            raise ConversionError(f"unsupported file extension: {source.suffix}")

        errors: list[str] = []
        parser = None
        for tool in chain:
            try:
                with semaphores[semaphore_for(kind, tool)]:
                    parser = convert_by_tool(tool, work_source, output, args)
                break
            except Exception as exc:  # noqa: BLE001 - keep trying fallbacks
                errors.append(f"{tool}: {exc}")
        if not parser:
            raise ConversionError("; ".join(errors))

        if args.normalize:
            with semaphores["normalize"]:
                normalize_with_pandoc(output)
        if args.frontmatter:
            write_frontmatter(
                output,
                source,
                parser,
                source_root=item.root,
                source_relative_path=item.relative_path,
                ocr_used=bool(record["ocr_used"]),
                asr_used=bool(record["asr_used"]),
            )

        record["status"] = "ok"
        record["parser"] = parser
        record["error"] = None
    except Exception as exc:  # noqa: BLE001 - record all task failures
        record["error"] = str(exc)
    finally:
        record["duration_seconds"] = round(time.time() - started, 3)
    return record


def safe_prefix(path: Path, used: set[str]) -> Path:
    base = path.name or "input"
    candidate = base
    index = 2
    while candidate in used:
        candidate = f"{base}-{index}"
        index += 1
    used.add(candidate)
    return Path(candidate)


def collect_inputs(paths: list[Path], recursive: bool, include_root: bool) -> list[SourceItem]:
    items: list[SourceItem] = []
    used_prefixes: set[str] = set()
    for path in paths:
        path = path.expanduser().resolve()
        if path.is_dir():
            prefix = safe_prefix(path, used_prefixes) if include_root else Path()
            iterator = path.rglob("*") if recursive else path.glob("*")
            for file_path in iterator:
                if file_path.is_file() and not file_path.name.startswith(".") and file_path.suffix.lower() in SUPPORTED_EXTS:
                    items.append(SourceItem(path=file_path.resolve(), root=path, output_prefix=prefix))
        elif path.is_file() and not path.name.startswith("."):
            if path.suffix.lower() in SUPPORTED_EXTS:
                items.append(SourceItem(path=path, root=path.parent, output_prefix=Path()))
    return sorted({item: None for item in items}.keys(), key=lambda item: (str(item.output_prefix), str(item.relative_path)))


def render_index(summary: dict[str, object], output_root: Path) -> str:
    records = list(summary["records"])
    ok_records = [item for item in records if item["status"] == "ok"]
    failed_records = [item for item in records if item["status"] != "ok"]
    lines = [
        "# all2md Conversion Index",
        "",
        "This folder mirrors the original source-package structure. Use `manifest.json` for machine-readable mapping and this index for quick human review.",
        "",
        "## Summary",
        "",
        f"- Created at: `{summary['created_at']}`",
        f"- Inputs: `{summary['input_count']}`",
        f"- Converted: `{summary['ok_count']}`",
        f"- Failed: `{summary['failed_count']}`",
        "",
        "## Folder Map",
        "",
    ]

    by_folder: dict[str, list[dict[str, object]]] = {}
    for record in records:
        folder = str(Path(str(record["output_relative_path"])).parent)
        if folder == ".":
            folder = "(root)"
        by_folder.setdefault(folder, []).append(record)

    for folder in sorted(by_folder):
        lines.extend([f"### {folder}", ""])
        for record in sorted(by_folder[folder], key=lambda item: str(item["output_relative_path"])):
            source_rel = record["source_relative_path"]
            parser = record["parser"] or "-"
            status = record["status"]
            output_rel = str(record["output_relative_path"])
            if status == "ok":
                link = output_rel.replace(" ", "%20")
                lines.append(f"- [{output_rel}]({link}) <- `{source_rel}` (`{parser}`)")
            else:
                lines.append(f"- FAILED `{source_rel}`: {record['error']}")
        lines.append("")

    if failed_records:
        lines.extend(["## Failures", ""])
        for record in failed_records:
            lines.append(f"- `{record['source_relative_path']}`: {record['error']}")
        lines.append("")

    lines.extend(
        [
            "## Notes For Research And Consulting Work",
            "",
            "- Start from this index to understand the evidence package before reading individual files.",
            "- Prefer source-relative paths when citing or discussing materials.",
            "- Check `manifest.json` for hashes, parser choices, output paths, and conversion errors.",
            "- For large projects, review failures first; missing PDFs or decks often create evidence gaps.",
            "",
        ]
    )
    return "\n".join(lines)


def write_index(summary: dict[str, object], output_root: Path, index_path: Path) -> None:
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(render_index(summary, output_root), encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert mixed files to Markdown with bounded concurrency.")
    parser.add_argument("inputs", nargs="+", type=Path, help="Input files or directories")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=None,
        help="Output Markdown directory; defaults to this skill's output/<timestamp>-<source> folder",
    )
    parser.add_argument("--run-name", default=None, help="Optional name for the default output subfolder")
    parser.add_argument("--workers", type=int, default=4, help="Global worker count for light conversions")
    parser.add_argument("--pdf-workers", type=int, default=2, help="Concurrent PDF/OCR/OpenDataLoader jobs")
    parser.add_argument("--heavy-workers", type=int, default=1, help="Concurrent MinerU/Marker-style jobs")
    parser.add_argument("--asr-workers", type=int, default=1, help="Concurrent audio transcription jobs")
    parser.add_argument("--recursive", action=argparse.BooleanOptionalAction, default=True, help="Recurse into input directories")
    parser.add_argument("--include-root", action=argparse.BooleanOptionalAction, default=True, help="Include each input directory name in the output tree")
    parser.add_argument("--frontmatter", action=argparse.BooleanOptionalAction, default=True, help="Add YAML front matter")
    parser.add_argument("--normalize", action=argparse.BooleanOptionalAction, default=True, help="Normalize Markdown with Pandoc when available")
    parser.add_argument("--force-ocr", action="store_true", help="Run OCRmyPDF before PDF conversion")
    parser.add_argument("--large-pdf-mb", type=int, default=50, help="PDFs at or above this size skip Docling in auto mode")
    parser.add_argument("--pdf-mode", choices=["auto", "docling", "pypdf-lite", "markitdown", "opendataloader-pdf", "marker", "mineru"], default="auto")
    parser.add_argument("--doc-mode", choices=["auto", "docling", "markitdown"], default="auto")
    parser.add_argument("--image-mode", choices=["auto", "docling", "tesseract-ocr"], default="auto")
    parser.add_argument("--asr-mode", choices=["auto", "local-whisper", "faster-whisper", "whisperx"], default="auto")
    parser.add_argument("--asr-model", default="medium", help="Whisper model name")
    parser.add_argument(
        "--whisper-url",
        default=os.environ.get("ALL2MD_WHISPER_URL", "http://127.0.0.1:9000/v1/audio/transcriptions"),
        help="Local Whisper transcription endpoint; defaults to ALL2MD_WHISPER_URL or an OpenAI-compatible localhost URL",
    )
    parser.add_argument(
        "--whisper-noproxy",
        default=os.environ.get("ALL2MD_WHISPER_NOPROXY", "*"),
        help="Value passed to curl --noproxy for local/Tailscale Whisper requests; empty string disables it",
    )
    parser.add_argument("--language", default="zh", help="ASR language code, or empty string for auto")
    parser.add_argument("--manifest", type=Path, default=None, help="Manifest JSON path; defaults to output-dir/manifest.json")
    parser.add_argument("--index", type=Path, default=None, help="Markdown index path; defaults to output-dir/INDEX.md")
    parser.add_argument("--no-index", action="store_true", help="Do not write INDEX.md")
    return parser.parse_args(argv)


def slugify(value: str) -> str:
    cleaned = []
    for char in value.strip():
        if char.isalnum():
            cleaned.append(char)
        elif char in {"-", "_"}:
            cleaned.append(char)
        elif char.isspace() or char in {".", "/", "\\"}:
            cleaned.append("-")
    slug = "".join(cleaned).strip("-_")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug[:80] or "sources"


def default_run_name(inputs: list[Path], requested: str | None) -> str:
    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    if requested:
        source = requested
    elif len(inputs) == 1:
        source = inputs[0].expanduser().resolve().stem
    else:
        source = "multi-source"
    return f"{timestamp}-{slugify(source)}"


def resolve_output_root(args: argparse.Namespace) -> Path:
    if args.output_dir:
        return args.output_dir.expanduser().resolve()
    return (SKILL_DIR / "output" / default_run_name(args.inputs, args.run_name)).resolve()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    output_root = resolve_output_root(args)
    output_root.mkdir(parents=True, exist_ok=True)
    manifest_path = (args.manifest or (output_root / "manifest.json")).expanduser().resolve()
    index_path = (args.index or (output_root / "INDEX.md")).expanduser().resolve()
    items = collect_inputs(args.inputs, args.recursive, args.include_root)
    if not items:
        print("No supported files found.", file=sys.stderr)
        return 2

    semaphores = {
        "light": threading.Semaphore(max(1, args.workers)),
        "pdf": threading.Semaphore(max(1, args.pdf_workers)),
        "heavy": threading.Semaphore(max(1, args.heavy_workers)),
        "asr": threading.Semaphore(max(1, args.asr_workers)),
        "video": threading.Semaphore(max(1, args.asr_workers)),
        "normalize": threading.Semaphore(max(1, args.workers)),
    }

    max_workers = max(1, args.workers + args.pdf_workers + args.heavy_workers + args.asr_workers)
    records: list[dict[str, object]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(convert_one, item, output_root, args, semaphores): item.path
            for item in items
        }
        for future in concurrent.futures.as_completed(futures):
            record = future.result()
            records.append(record)
            status = record["status"]
            parser = record["parser"] or "-"
            print(f"[{status}] {parser} {record['source_path']} -> {record['output_path']}")
            if record["error"]:
                print(f"  error: {record['error']}", file=sys.stderr)

    records.sort(key=lambda item: str(item["source_path"]))
    source_roots = sorted({str(item.root) for item in items})
    summary = {
        "created_at": dt.datetime.now(dt.UTC).isoformat(),
        "source_roots": source_roots,
        "output_root": str(output_root),
        "input_count": len(items),
        "ok_count": sum(1 for item in records if item["status"] == "ok"),
        "failed_count": sum(1 for item in records if item["status"] != "ok"),
        "records": records,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    if not args.no_index:
        write_index(summary, output_root, index_path)
        print(f"Index: {index_path}")
    print(f"Manifest: {manifest_path}")
    return 0 if summary["failed_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
