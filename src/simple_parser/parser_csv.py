"""Parse CSV files to Markdown tables."""

import csv
from pathlib import Path

from simple_parser import md


def parse(path: str) -> str:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        return ""

    headers = rows[0]
    data = [row for row in rows[1:] if any(cell.strip() for cell in row)]

    return md.table(headers, data)
