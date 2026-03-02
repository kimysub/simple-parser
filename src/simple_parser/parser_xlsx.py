"""XLSX -> Markdown parser.

XLSX files are ZIP archives containing XML. Key files:
- xl/sharedStrings.xml: string table (cells reference by index)
- xl/workbook.xml: sheet names
- xl/worksheets/sheet{N}.xml: cell data
"""

import re
import zipfile
import xml.etree.ElementTree as ET

from simple_parser import md

SS_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

_COL_RE = re.compile(r"^([A-Z]+)")


def _col_to_index(col_str: str) -> int:
    """Convert column letter(s) to 0-based index. A=0, B=1, ..., Z=25, AA=26."""
    result = 0
    for ch in col_str:
        result = result * 26 + (ord(ch) - ord("A") + 1)
    return result - 1


def _cell_col_index(cell_ref: str) -> int:
    """Extract column index from cell reference like 'A1', 'BC12'."""
    m = _COL_RE.match(cell_ref)
    if m:
        return _col_to_index(m.group(1))
    return 0


def _load_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    """Load shared string table from xl/sharedStrings.xml."""
    try:
        data = zf.read("xl/sharedStrings.xml")
    except KeyError:
        return []

    root = ET.fromstring(data)
    strings: list[str] = []
    for si in root.findall(f"{{{SS_NS}}}si"):
        # A shared string can have a single <t> or rich text <r>/<t> elements
        parts = []
        for t in si.iter(f"{{{SS_NS}}}t"):
            if t.text:
                parts.append(t.text)
        strings.append("".join(parts))
    return strings


def _load_sheet_names(zf: zipfile.ZipFile) -> list[tuple[str, str]]:
    """Return list of (sheet name, rId) from workbook.xml."""
    data = zf.read("xl/workbook.xml")
    root = ET.fromstring(data)
    result: list[tuple[str, str]] = []
    for sheet in root.iter(f"{{{SS_NS}}}sheet"):
        name = sheet.get("name", "")
        r_id = sheet.get(f"{{{R_NS}}}id", "")
        result.append((name, r_id))
    return result


def _load_sheet_targets(zf: zipfile.ZipFile) -> dict[str, str]:
    """Return {rId: target_path} from xl/_rels/workbook.xml.rels."""
    try:
        data = zf.read("xl/_rels/workbook.xml.rels")
    except KeyError:
        return {}
    root = ET.fromstring(data)
    result: dict[str, str] = {}
    for rel in root:
        r_id = rel.get("Id", "")
        target = rel.get("Target", "")
        result[r_id] = target
    return result


def _parse_sheet(sheet_xml: bytes, shared_strings: list[str]) -> list[list[str]]:
    """Parse a sheet XML into a 2D list of string values."""
    root = ET.fromstring(sheet_xml)
    rows_dict: dict[int, dict[int, str]] = {}
    max_col = 0

    for row in root.iter(f"{{{SS_NS}}}row"):
        row_num = int(row.get("r", "0"))
        for cell in row.findall(f"{{{SS_NS}}}c"):
            ref = cell.get("r", "")
            col_idx = _cell_col_index(ref)
            max_col = max(max_col, col_idx)

            v_elem = cell.find(f"{{{SS_NS}}}v")
            if v_elem is None or v_elem.text is None:
                value = ""
            elif cell.get("t") == "s":
                # Shared string reference
                idx = int(v_elem.text)
                value = shared_strings[idx] if idx < len(shared_strings) else ""
            else:
                value = v_elem.text

            if row_num not in rows_dict:
                rows_dict[row_num] = {}
            rows_dict[row_num][col_idx] = value

    if not rows_dict:
        return []

    # Convert to dense 2D list
    num_cols = max_col + 1
    result: list[list[str]] = []
    for row_num in sorted(rows_dict):
        row_data = rows_dict[row_num]
        row_list = [row_data.get(c, "") for c in range(num_cols)]
        result.append(row_list)
    return result


def parse(path: str) -> str:
    """Parse a .xlsx file and return Markdown content."""
    blocks: list[str] = []

    with zipfile.ZipFile(path) as zf:
        shared_strings = _load_shared_strings(zf)
        sheet_names = _load_sheet_names(zf)
        sheet_targets = _load_sheet_targets(zf)

        for name, r_id in sheet_names:
            target = sheet_targets.get(r_id, "")
            if not target:
                continue
            sheet_path = f"xl/{target}"

            try:
                sheet_xml = zf.read(sheet_path)
            except KeyError:
                continue

            data = _parse_sheet(sheet_xml, shared_strings)
            if not data:
                continue

            blocks.append(md.heading(f"Sheet: {name}", 2))
            headers = data[0]
            rows = data[1:]
            blocks.append(md.table(headers, rows))

    return "\n\n".join(blocks)
