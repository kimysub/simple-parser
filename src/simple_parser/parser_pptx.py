"""PPTX -> Markdown parser.

PPTX files are ZIP archives. Slides are in ppt/slides/slide{N}.xml.
Slide order is determined from ppt/presentation.xml relationships.
Tables in slides are inside p:graphicFrame elements using a:tbl (DrawingML).
"""

import re
import zipfile
import xml.etree.ElementTree as ET

from simple_parser import md

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

_SLIDE_NUM_RE = re.compile(r"slide(\d+)\.xml$")


def _get_slide_paths(zf: zipfile.ZipFile) -> list[str]:
    """Return slide XML paths in presentation order."""
    # Try to use presentation.xml.rels for ordering
    try:
        rels_data = zf.read("ppt/_rels/presentation.xml.rels")
        rels_root = ET.fromstring(rels_data)
        slide_targets = []
        for rel in rels_root:
            target = rel.get("Target", "")
            if "slides/slide" in target:
                slide_targets.append(f"ppt/{target}")
        if slide_targets:
            # Sort by slide number
            slide_targets.sort(
                key=lambda p: int(_SLIDE_NUM_RE.search(p).group(1))
            )
            return slide_targets
    except (KeyError, ET.ParseError):
        pass

    # Fallback: find slide files directly
    paths = [n for n in zf.namelist() if _SLIDE_NUM_RE.search(n)]
    paths.sort(key=lambda p: int(_SLIDE_NUM_RE.search(p).group(1)))
    return paths


def _extract_text(elem: ET.Element) -> str:
    """Extract all a:t text from an element tree."""
    texts = []
    for t in elem.iter(f"{{{A_NS}}}t"):
        if t.text:
            texts.append(t.text)
    raw = " ".join(texts)
    # Collapse multiple spaces (common in PPTX with split text runs)
    return re.sub(r" {2,}", " ", raw)


def _parse_table(tbl: ET.Element) -> str:
    """Convert an a:tbl (DrawingML table) element to a markdown table."""
    rows: list[list[str]] = []
    for tr in tbl.findall(f"{{{A_NS}}}tr"):
        cells: list[str] = []
        for tc in tr.findall(f"{{{A_NS}}}tc"):
            cell_text = _extract_text(tc).strip()
            cells.append(cell_text)
        rows.append(cells)

    if not rows:
        return ""

    headers = rows[0]
    data_rows = rows[1:]
    return md.table(headers, data_rows)


def _parse_slide(slide_xml: bytes, slide_num: int) -> str:
    """Parse a single slide XML and return markdown."""
    root = ET.fromstring(slide_xml)
    title = ""
    body_parts: list[str] = []
    table_parts: list[str] = []

    # Find shapes (p:sp) for title and body text
    for sp in root.iter(f"{{{P_NS}}}sp"):
        # Check if this shape is a title placeholder
        nv_pr = sp.find(f".//{{{P_NS}}}nvPr")
        is_title = False
        if nv_pr is not None:
            ph = nv_pr.find(f"{{{P_NS}}}ph")
            if ph is not None:
                ph_type = ph.get("type", "")
                if ph_type in ("title", "ctrTitle"):
                    is_title = True

        tx_body = sp.find(f".//{{{P_NS}}}txBody")
        if tx_body is None:
            continue

        text = _extract_text(tx_body).strip()
        if not text:
            continue

        if is_title:
            title = text
        else:
            body_parts.append(text)

    # Find tables inside graphicFrame elements
    for gf in root.iter(f"{{{P_NS}}}graphicFrame"):
        for tbl in gf.iter(f"{{{A_NS}}}tbl"):
            table_md = _parse_table(tbl)
            if table_md:
                table_parts.append(table_md)

    lines: list[str] = []
    if title:
        lines.append(md.heading(f"Slide {slide_num}: {title}", 2))
    else:
        lines.append(md.heading(f"Slide {slide_num}", 2))

    for part in body_parts:
        lines.append(part)

    for table in table_parts:
        lines.append(table)

    return "\n\n".join(lines)


def parse(path: str) -> str:
    """Parse a .pptx file and return Markdown content."""
    blocks: list[str] = []

    with zipfile.ZipFile(path) as zf:
        slide_paths = _get_slide_paths(zf)
        for i, sp in enumerate(slide_paths, 1):
            slide_xml = zf.read(sp)
            slide_md = _parse_slide(slide_xml, i)
            if slide_md.strip():
                blocks.append(slide_md)

    return "\n\n".join(blocks)
