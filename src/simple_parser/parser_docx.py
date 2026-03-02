"""DOCX -> Markdown parser.

DOCX files are ZIP archives containing XML. The main content is in
word/document.xml using the OOXML wordprocessingml namespace.
"""

import re
import zipfile
import xml.etree.ElementTree as ET

from simple_parser import md

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_NS = {"w": W}

_HEADING_RE = re.compile(r"^Heading(\d+)$", re.IGNORECASE)


def _get_text(run_elem: ET.Element) -> str:
    """Extract concatenated text from all w:t elements in a run."""
    return "".join(t.text or "" for t in run_elem.findall(f"{{{W}}}t"))


def _run_to_md(run_elem: ET.Element) -> str:
    """Convert a single w:r element to markdown text with bold/italic."""
    text = _get_text(run_elem)
    if not text:
        return ""
    rpr = run_elem.find(f"{{{W}}}rPr")
    if rpr is not None:
        is_bold = rpr.find(f"{{{W}}}b") is not None
        is_italic = rpr.find(f"{{{W}}}i") is not None
        if is_bold:
            text = md.bold(text)
        if is_italic:
            text = md.italic(text)
    return text


def _paragraph_text(p: ET.Element) -> str:
    """Get full markdown text of a paragraph from its runs."""
    return "".join(_run_to_md(r) for r in p.findall(f"{{{W}}}r"))


def _get_heading_level(p: ET.Element) -> int | None:
    """Return heading level (1-6) if paragraph has a Heading style, else None."""
    ppr = p.find(f"{{{W}}}pPr")
    if ppr is None:
        return None
    pstyle = ppr.find(f"{{{W}}}pStyle")
    if pstyle is None:
        return None
    val = pstyle.get(f"{{{W}}}val", "")
    m = _HEADING_RE.match(val)
    if m:
        return min(int(m.group(1)), 6)
    return None


def _get_num_info(p: ET.Element) -> tuple[str | None, int]:
    """Return (numId, ilvl) if paragraph is a list item, else (None, 0)."""
    ppr = p.find(f"{{{W}}}pPr")
    if ppr is None:
        return None, 0
    num_pr = ppr.find(f"{{{W}}}numPr")
    if num_pr is None:
        return None, 0
    num_id_elem = num_pr.find(f"{{{W}}}numId")
    ilvl_elem = num_pr.find(f"{{{W}}}ilvl")
    num_id = num_id_elem.get(f"{{{W}}}val") if num_id_elem is not None else None
    ilvl = int(ilvl_elem.get(f"{{{W}}}val", "0")) if ilvl_elem is not None else 0
    return num_id, ilvl


def _load_numbering(zf: zipfile.ZipFile) -> dict[str, str]:
    """Load numbering.xml and return {numId: format} mapping.

    format is 'bullet' or 'decimal' (or other numFmt values).
    """
    try:
        data = zf.read("word/numbering.xml")
    except KeyError:
        return {}

    root = ET.fromstring(data)
    # Map abstractNumId -> numFmt
    abstract_fmt: dict[str, str] = {}
    for abstract in root.findall(f"{{{W}}}abstractNum"):
        abs_id = abstract.get(f"{{{W}}}abstractNumId", "")
        lvl = abstract.find(f"{{{W}}}lvl")
        if lvl is not None:
            fmt_elem = lvl.find(f"{{{W}}}numFmt")
            if fmt_elem is not None:
                abstract_fmt[abs_id] = fmt_elem.get(f"{{{W}}}val", "bullet")

    # Map numId -> abstractNumId -> numFmt
    result: dict[str, str] = {}
    for num in root.findall(f"{{{W}}}num"):
        num_id = num.get(f"{{{W}}}numId", "")
        abs_ref = num.find(f"{{{W}}}abstractNumId")
        if abs_ref is not None:
            abs_id = abs_ref.get(f"{{{W}}}val", "")
            result[num_id] = abstract_fmt.get(abs_id, "bullet")
    return result


def _parse_table(tbl: ET.Element) -> str:
    """Convert a w:tbl element to a markdown table."""
    rows: list[list[str]] = []
    for tr in tbl.findall(f"{{{W}}}tr"):
        cells: list[str] = []
        for tc in tr.findall(f"{{{W}}}tc"):
            # Each cell can have multiple paragraphs; join with space
            parts = []
            for p in tc.findall(f"{{{W}}}p"):
                text = _paragraph_text(p)
                if text:
                    parts.append(text)
            cells.append(" ".join(parts))
        rows.append(cells)

    if not rows:
        return ""

    # First row as headers
    headers = rows[0]
    data_rows = rows[1:]
    return md.table(headers, data_rows)


def parse(path: str) -> str:
    """Parse a .docx file and return Markdown content."""
    blocks: list[str] = []
    # Track list state for numbered lists
    ordered_counters: dict[str, int] = {}

    with zipfile.ZipFile(path) as zf:
        numbering = _load_numbering(zf)
        doc_xml = zf.read("word/document.xml")

    root = ET.fromstring(doc_xml)
    body = root.find(f"{{{W}}}body")
    if body is None:
        return ""

    for elem in body:
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

        if tag == "tbl":
            blocks.append(_parse_table(elem))
            continue

        if tag != "p":
            continue

        # Check heading
        level = _get_heading_level(elem)
        text = _paragraph_text(elem)

        if level is not None and text:
            blocks.append(md.heading(text, level))
            continue

        # Check list
        num_id, ilvl = _get_num_info(elem)
        if num_id is not None and text:
            indent = "  " * ilvl
            fmt = numbering.get(num_id, "bullet")
            if fmt == "bullet":
                blocks.append(f"{indent}- {text}")
            else:
                key = f"{num_id}-{ilvl}"
                ordered_counters[key] = ordered_counters.get(key, 0) + 1
                blocks.append(f"{indent}{ordered_counters[key]}. {text}")
            continue

        # Regular paragraph
        if text:
            blocks.append(text)

    return "\n\n".join(blocks)
