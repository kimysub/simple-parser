"""Post-processor that converts Markdown to clean text optimized for RAG embedding.

Markdown formatting (headings, bold, italic, tables, links, etc.) is noise
for embedding models. This module strips formatting and linearizes tables
into key-value rows that embedding models can understand.
"""

import re

# Markdown table row pattern: | cell1 | cell2 | ... |
_TABLE_ROW_RE = re.compile(r"^\|(.+)\|$")
_TABLE_SEP_RE = re.compile(r"^\|\s*[-:]+[\s|:-]*\|$")
_HEADING_RE = re.compile(r"^#{1,6}\s+")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_ITALIC_RE = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")
_INLINE_CODE_RE = re.compile(r"`([^`]+)`")
_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")
_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]*)\)")
_SLIDE_PREFIX_RE = re.compile(r"^Slide\s+\d+:\s*")


def _linearize_table(lines: list[str]) -> str:
    """Convert markdown table lines to key-value rows.

    | Name | Age |
    | --- | --- |
    | Alice | 30 |

    becomes:

    Name: Alice; Age: 30
    """
    headers: list[str] = []
    rows: list[str] = []

    for line in lines:
        if _TABLE_SEP_RE.match(line):
            continue

        m = _TABLE_ROW_RE.match(line)
        if not m:
            continue

        cells = [c.strip() for c in m.group(1).split("|")]

        if not headers:
            headers = cells
        else:
            parts = []
            for i, cell in enumerate(cells):
                if not cell:
                    continue
                if i < len(headers) and headers[i]:
                    parts.append(f"{headers[i]}: {cell}")
                else:
                    parts.append(cell)
            if parts:
                rows.append("; ".join(parts))

    return "\n".join(rows)


def clean_for_rag(markdown: str) -> str:
    """Convert markdown to clean text optimized for RAG embedding.

    - Tables → linearized key-value rows (Name: Alice; Age: 30)
    - Headings → plain text (no # markers)
    - Bold/italic → plain text (no ** or * markers)
    - Links → text with URL (no bracket syntax)
    - Images → descriptive text
    - Horizontal rules → removed
    - Code blocks → plain text
    - Slide numbering → stripped
    """
    lines = markdown.split("\n")
    result: list[str] = []
    table_buffer: list[str] = []
    in_code_block = False

    for line in lines:
        # Handle code blocks
        if line.strip().startswith("```"):
            if in_code_block:
                in_code_block = False
            else:
                in_code_block = True
            continue

        if in_code_block:
            result.append(line)
            continue

        # Collect table lines
        if _TABLE_ROW_RE.match(line.strip()):
            table_buffer.append(line.strip())
            continue

        # Flush table buffer when non-table line appears
        if table_buffer:
            linearized = _linearize_table(table_buffer)
            if linearized:
                result.append(linearized)
            table_buffer = []

        stripped = line.strip()

        # Skip horizontal rules
        if stripped in ("---", "***", "___"):
            continue

        # Skip separator-only lines from tables
        if _TABLE_SEP_RE.match(stripped):
            continue

        # Strip heading markers
        stripped = _HEADING_RE.sub("", stripped)

        # Strip slide number prefixes (e.g., "Slide 1: Title" → "Title")
        stripped = _SLIDE_PREFIX_RE.sub("", stripped)

        # Strip image syntax → descriptive text
        stripped = _IMAGE_RE.sub(r"\1", stripped)

        # Strip link syntax → text with URL
        stripped = _LINK_RE.sub(r"\1 (\2)", stripped)

        # Strip bold markers
        stripped = _BOLD_RE.sub(r"\1", stripped)

        # Strip italic markers
        stripped = _ITALIC_RE.sub(r"\1", stripped)

        # Strip inline code markers
        stripped = _INLINE_CODE_RE.sub(r"\1", stripped)

        result.append(stripped)

    # Flush remaining table buffer
    if table_buffer:
        linearized = _linearize_table(table_buffer)
        if linearized:
            result.append(linearized)

    # Join and normalize whitespace
    text = "\n".join(result)
    # Collapse 3+ newlines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
