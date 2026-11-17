"""图片识别与文档文字提取。"""

from __future__ import annotations

import io
from pathlib import Path

IMAGE_EXTS = {"png", "jpg", "jpeg", "webp", "gif"}
DOC_EXTS = {"pdf", "docx", "xlsx", "pptx", "txt", "md", "csv", "json"}

MAX_CHARS = 30_000
MAX_PDF_PAGES = 50
MAX_SHEET_ROWS = 500
MAX_SLIDES = 100

_MEDIA_TYPES = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
    "gif": "image/gif",
}


def suffix(name: str) -> str:
    return Path(name).suffix.lower().lstrip(".")


def is_image(name: str) -> bool:
    return suffix(name) in IMAGE_EXTS


def image_media_type(name: str) -> str:
    return _MEDIA_TYPES.get(suffix(name), "application/octet-stream")


def extract_text(name: str, data: bytes) -> tuple[str, str | None]:
    """提取文档文字，返回 (文本, 错误信息)。"""
    ext = suffix(name)
    try:
        if ext == "pdf":
            text = _pdf_text(data)
        elif ext == "docx":
            text = _docx_text(data)
        elif ext == "xlsx":
            text = _xlsx_text(data)
        elif ext == "pptx":
            text = _pptx_text(data)
        elif ext in {"txt", "md", "csv", "json"}:
            text = data.decode("utf-8", errors="replace")
        else:
            return "", f"不支持的文件格式 .{ext}"
    except Exception as exc:
        return "", f"解析失败（{type(exc).__name__}）：{exc}"

    text = text.strip()
    if not text:
        return "", "未提取到文字内容"
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + "\n\n（内容过长，已截断）"
    return text, None


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    parts = []
    for index, page in enumerate(reader.pages):
        if index >= MAX_PDF_PAGES:
            parts.append(f"（仅解析前 {MAX_PDF_PAGES} 页）")
            break
        parts.append(page.extract_text() or "")
    return "\n\n".join(parts)


def _docx_text(data: bytes) -> str:
    from docx import Document

    doc = Document(io.BytesIO(data))
    parts = [p.text for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            if any(cells):
                parts.append("\t".join(cells))
    return "\n".join(parts)


def _xlsx_text(data: bytes) -> str:
    from openpyxl import load_workbook

    workbook = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    parts = []
    for sheet in workbook.worksheets:
        parts.append(f"## 工作表：{sheet.title}")
        for index, row in enumerate(sheet.iter_rows(values_only=True)):
            if index >= MAX_SHEET_ROWS:
                parts.append(f"（仅解析前 {MAX_SHEET_ROWS} 行）")
                break
            values = ["" if value is None else str(value) for value in row]
            if any(values):
                parts.append("\t".join(values))
    workbook.close()
    return "\n".join(parts)


def _pptx_text(data: bytes) -> str:
    from pptx import Presentation

    presentation = Presentation(io.BytesIO(data))
    parts = []
    for index, slide in enumerate(presentation.slides, start=1):
        if index > MAX_SLIDES:
            parts.append(f"（仅解析前 {MAX_SLIDES} 页）")
            break
        texts = [
            shape.text_frame.text.strip()
            for shape in slide.shapes
            if getattr(shape, "has_text_frame", False) and shape.text_frame.text.strip()
        ]
        if texts:
            parts.append(f"## 幻灯片 {index}\n" + "\n".join(texts))
    return "\n\n".join(parts)
