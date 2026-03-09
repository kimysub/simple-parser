"""PDF -> Markdown parser.

Uses PyMuPDF (fitz) for non-OCR text extraction.
Heading detection via font-size heuristic: text larger than the
modal (most common) body font size is treated as a heading.
Table detection via page.find_tables() for structured table extraction,
plus text-based fallback for borderless tables (common in academic papers).
"""

import re
from collections import Counter

import fitz

from simple_parser import md

# Minimum character ratio to treat a font size as heading vs body
_HEADING_RATIO_MIN = 1.2
# Maximum text length to treat as a heading (long text = paragraph, not heading)
_HEADING_MAX_LEN = 200
# Minimum text length to treat as a heading (very short text = label, not heading)
_HEADING_MIN_LEN = 10

# Common typographic ligatures to normalize
_LIGATURES = {"\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi", "\ufb04": "ffl"}


def _detect_body_size(doc: fitz.Document) -> float:
    """Find the effective body font size across all pages.

    Rounds sizes to nearest integer to merge rendering variations,
    then uses the largest size with significant share (>5% of chars)
    to avoid treating common sub-heading sizes as headings.
    """
    size_counter: Counter[int] = Counter()
    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if text:
                        size = round(span.get("size", 0))
                        size_counter[size] += len(text)
    if not size_counter:
        return 12.0
    total = sum(size_counter.values())
    # Require both >5% share and >200 chars to be considered body text
    body_sizes = [s for s, c in size_counter.items() if c >= total * 0.05 and c >= 200]
    return float(max(body_sizes)) if body_sizes else float(size_counter.most_common(1)[0][0])


def _size_to_heading_level(size: float, body_size: float) -> int | None:
    """Map font size to heading level relative to body size.

    Returns 1-3 based on how much larger the text is, or None for body text.
    """
    if size < body_size * _HEADING_RATIO_MIN:
        return None
    ratio = size / body_size
    if ratio >= 1.8:
        return 1
    if ratio >= 1.4:
        return 2
    return 3


def _rect_overlaps(r1: fitz.Rect, r2: fitz.Rect) -> bool:
    """Check if two rectangles overlap significantly (>50% of smaller area)."""
    ix0 = max(r1.x0, r2.x0)
    iy0 = max(r1.y0, r2.y0)
    ix1 = min(r1.x1, r2.x1)
    iy1 = min(r1.y1, r2.y1)
    if ix0 >= ix1 or iy0 >= iy1:
        return False
    intersection = (ix1 - ix0) * (iy1 - iy0)
    r2_area = (r2.x1 - r2.x0) * (r2.y1 - r2.y0)
    if r2_area <= 0:
        return False
    return intersection / r2_area > 0.5


def _block_in_table(block: dict, table_rects: list[fitz.Rect]) -> bool:
    """Check if a text block overlaps with any table region."""
    bbox = block.get("bbox")
    if not bbox:
        return False
    block_rect = fitz.Rect(bbox)
    return any(_rect_overlaps(tr, block_rect) for tr in table_rects)


def _extract_tables(page: fitz.Page) -> tuple[list[str], list[fitz.Rect]]:
    """Extract tables from a page as markdown, return (table_markdowns, table_rects)."""
    tables_md: list[str] = []
    table_rects: list[fitz.Rect] = []

    finder = page.find_tables()
    for table in finder.tables:
        table_rects.append(fitz.Rect(table.bbox))
        data = table.extract()
        if not data:
            continue

        cleaned = []
        for row in data:
            cleaned.append([cell if cell is not None else "" for cell in row])

        if len(cleaned) < 1:
            continue

        headers = cleaned[0]
        data_rows = cleaned[1:]
        tables_md.append(md.table(headers, data_rows))

    return tables_md, table_rects


def _extract_block_lines(block: dict) -> list[str]:
    """Extract individual lines of text from a block."""
    result = []
    for line in block.get("lines", []):
        parts = []
        for span in line.get("spans", []):
            parts.append(span.get("text", ""))
        text = "".join(parts).strip()
        if text:
            result.append(text)
    return result


def _detect_borderless_tables(blocks: list[dict], table_rects: list[fitz.Rect]) -> list[tuple[set[int], str]]:
    """Detect borderless tables from text blocks (common in academic papers).

    Looks for patterns like:
      Block: "Table N: Title"
      Block: "Header1  Header2  Header3"  (short, multi-column header)
      Block: "Val1  Val2  Val3\nVal4  Val5  Val6"  (data rows)

    Returns list of (block_indices_to_skip, markdown_table).
    """
    results = []
    table_label_re = re.compile(r"^Table\s+\d+[.:]\s*")

    i = 0
    while i < len(blocks):
        block = blocks[i]
        if block.get("type") != 0:
            i += 1
            continue

        # Skip blocks inside bordered tables
        if table_rects and _block_in_table(block, table_rects):
            i += 1
            continue

        lines = _extract_block_lines(block)
        full_text = " ".join(lines)

        # Look for "Table N:" label
        if not table_label_re.match(full_text):
            i += 1
            continue

        # Found a table label. Look ahead for header + data blocks.
        skip_indices = {i}
        header_block_idx = None
        data_block_idx = None

        # Next 1-2 blocks should be header and data
        for j in range(i + 1, min(i + 3, len(blocks))):
            b = blocks[j]
            if b.get("type") != 0:
                continue
            b_lines = _extract_block_lines(b)
            if not b_lines:
                continue

            # Header block: short lines with column names (up to ~10 cols)
            if header_block_idx is None and len(b_lines) <= 10:
                header_block_idx = j
                skip_indices.add(j)
                continue

            # Data block: multiple lines or follows header
            if header_block_idx is not None and data_block_idx is None:
                data_block_idx = j
                skip_indices.add(j)
                break

        if header_block_idx is not None and data_block_idx is not None:
            header_lines = _extract_block_lines(blocks[header_block_idx])
            data_lines = _extract_block_lines(blocks[data_block_idx])

            # Detect columns: try space-split first, fall back to per-line
            header_text = " ".join(header_lines)
            headers = re.split(r"\s{2,}", header_text.strip())

            # If space-split fails, treat each line as a column header
            if len(headers) < 2 and len(header_lines) >= 2:
                headers = [h.strip() for h in header_lines]

            if len(headers) < 2:
                i += 1
                continue

            n_cols = len(headers)
            rows = []

            # Try per-line grouping (each cell on its own line)
            if all(len(re.split(r"\s{2,}", dl.strip())) == 1 for dl in data_lines):
                for k in range(0, len(data_lines) - n_cols + 1, n_cols):
                    row = [data_lines[k + c].strip() for c in range(n_cols)]
                    rows.append(row)
            else:
                # Space-split approach
                for dl in data_lines:
                    cells = re.split(r"\s{2,}", dl.strip())
                    if len(cells) >= n_cols - 1:
                        cells = cells[:n_cols]
                        while len(cells) < n_cols:
                            cells.append("")
                        rows.append(cells)

            if rows:
                caption = f"**{full_text}**\n\n"
                results.append((skip_indices, caption + md.table(headers, rows)))

        i += 1

    return results


def parse(path: str) -> str:
    """Parse a .pdf file and return Markdown content."""
    doc = fitz.open(path)
    body_size = _detect_body_size(doc)

    page_blocks: list[str] = []

    for page in doc:
        lines: list[str] = []

        # Extract bordered tables first
        tables_md, table_rects = _extract_tables(page)

        blocks = page.get_text("dict")["blocks"]

        # Detect borderless tables
        borderless = _detect_borderless_tables(blocks, table_rects)
        skip_block_indices: set[int] = set()
        for indices, table_md in borderless:
            skip_block_indices.update(indices)
            tables_md.append(table_md)

        # Extract text, skipping table blocks
        for block_idx, block in enumerate(blocks):
            if block.get("type") != 0:
                continue

            if block_idx in skip_block_indices:
                continue

            if table_rects and _block_in_table(block, table_rects):
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

                level = _size_to_heading_level(round(max_size), body_size)
                if level is not None:
                    block_heading_level = level

                block_lines.append(line_text)

            text = " ".join(block_lines)
            # Collapse multiple spaces (common in PDF with positioned text)
            text = re.sub(r" {2,}", " ", text)
            if not text:
                continue

            # Don't treat long text as headings (paragraphs aren't headings)
            # Don't treat very short text as headings (labels aren't headings)
            if block_heading_level is not None and not (_HEADING_MIN_LEN <= len(text) <= _HEADING_MAX_LEN):
                block_heading_level = None

            if block_heading_level is not None:
                lines.append(md.heading(text, block_heading_level))
            else:
                lines.append(text)

        lines.extend(tables_md)

        if lines:
            page_blocks.append("\n\n".join(lines))

    doc.close()
    result = "\n\n---\n\n".join(page_blocks)
    for lig, repl in _LIGATURES.items():
        result = result.replace(lig, repl)
    return result
