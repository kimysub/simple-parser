"""Parse .xls (BIFF) spreadsheet files to Markdown using xlrd."""

import xlrd

from simple_parser import md


def parse(path: str) -> str:
    wb = xlrd.open_workbook(path)
    blocks: list[str] = []

    for sheet in wb.sheets():
        blocks.append(md.heading(f"Sheet: {sheet.name}", 2))
        if sheet.nrows == 0:
            continue

        headers: list[str] = []
        for c in range(sheet.ncols):
            v = sheet.cell_value(0, c)
            if isinstance(v, float) and v == int(v):
                v = int(v)
            headers.append(str(v))

        rows: list[list[str]] = []
        for r in range(1, sheet.nrows):
            row: list[str] = []
            for c in range(sheet.ncols):
                v = sheet.cell_value(r, c)
                if isinstance(v, float) and v == int(v):
                    v = int(v)
                row.append(str(v))
            rows.append(row)

        blocks.append(md.table(headers, rows))

    return "\n\n".join(blocks)
