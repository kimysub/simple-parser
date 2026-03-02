"""PDF -> Markdown parser.

Uses PyMuPDF (fitz) for non-OCR text extraction.
Heading detection via font-size heuristic: text larger than the
modal (most common) body font size is treated as a heading.
"""

from collections import Counter

import fitz

from simple_parser import md


def _detect_body_size(doc: fitz.Document) -> float:
    """Find the most common font size across all pages (modal body size)."""
    size_counter: Counter[float] = Counter()
    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if block.get("type") != 0:  # text blocks only
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if text:
                        size = round(span.get("size", 0), 1)
                        size_counter[size] += len(text)
    if not size_counter:
        return 12.0
    return size_counter.most_common(1)[0][0]


def _size_to_heading_level(size: float, body_size: float) -> int | None:
    """Map font size to heading level relative to body size.

    Returns 1-3 based on how much larger the text is, or None for body text.
    """
    if size <= body_size * 1.1:
        return None
    ratio = size / body_size
    if ratio >= 1.8:
        return 1
    if ratio >= 1.4:
        return 2
    return 3


def parse(path: str) -> str:
    """Parse a .pdf file and return Markdown content."""
    doc = fitz.open(path)
    body_size = _detect_body_size(doc)

    page_blocks: list[str] = []

    for page in doc:
        lines: list[str] = []
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if block.get("type") != 0:
                continue

            block_lines: list[str] = []
            block_heading_level: int | None = None

            for line in block.get("lines", []):
                line_text_parts: list[str] = []
                max_size = 0.0
                for span in line.get("spans", []):
                    text = span.get("text", "")
                    if text.strip():
                        max_size = max(max_size, span.get("size", 0))
                    line_text_parts.append(text)

                line_text = "".join(line_text_parts).strip()
                if not line_text:
                    continue

                level = _size_to_heading_level(max_size, body_size)
                if level is not None:
                    block_heading_level = level

                block_lines.append(line_text)

            text = " ".join(block_lines)
            if not text:
                continue

            if block_heading_level is not None:
                lines.append(md.heading(text, block_heading_level))
            else:
                lines.append(text)

        if lines:
            page_blocks.append("\n\n".join(lines))

    doc.close()
    return "\n\n---\n\n".join(page_blocks)
