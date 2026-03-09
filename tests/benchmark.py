"""Benchmark parsing quality on TEST_DOC files.

Scores each parser output on:
  - table_detection: expected tables found as markdown tables
  - heading_quality: heading count within expected range
  - whitespace: no excessive consecutive spaces
  - content: key phrases present in output
  - noise: no duplicate lines or garbage text

Run:  python tests/benchmark.py
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from simple_parser import parser_pdf, parser_pptx, parser_xlsx


def _count_md_tables(text: str) -> int:
    """Count markdown table blocks (header + separator + data)."""
    lines = text.split("\n")
    count = 0
    i = 0
    while i < len(lines) - 1:
        if (
            lines[i].strip().startswith("|")
            and i + 1 < len(lines)
            and re.match(r"^\|\s*[-:]+", lines[i + 1].strip())
        ):
            count += 1
            # skip to end of table
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                i += 1
        else:
            i += 1
    return count


def _count_headings(text: str) -> int:
    return sum(1 for line in text.split("\n") if re.match(r"^#{1,6}\s", line))


def _max_consecutive_spaces(text: str) -> int:
    matches = re.findall(r" {2,}", text)
    return max((len(m) for m in matches), default=1)


def _has_phrases(text: str, phrases: list[str]) -> tuple[int, int]:
    found = sum(1 for p in phrases if p in text)
    return found, len(phrases)


def score_document(name: str, text: str, expect: dict) -> dict:
    """Score a parsed document against expectations.

    expect keys:
      min_tables, max_tables: expected table count range
      min_headings, max_headings: expected heading count range
      max_spaces: maximum acceptable consecutive spaces
      key_phrases: list of phrases that should appear
      min_length: minimum output length
    """
    scores = {}

    # Table detection (0-100)
    n_tables = _count_md_tables(text)
    min_t = expect.get("min_tables", 0)
    max_t = expect.get("max_tables", 100)
    if min_t <= n_tables <= max_t:
        scores["tables"] = 100
    elif n_tables < min_t:
        scores["tables"] = max(0, int(100 * n_tables / min_t))
    else:
        scores["tables"] = max(0, int(100 * max_t / n_tables))

    # Heading quality (0-100)
    n_heads = _count_headings(text)
    min_h = expect.get("min_headings", 0)
    max_h = expect.get("max_headings", 100)
    if min_h <= n_heads <= max_h:
        scores["headings"] = 100
    elif n_heads < min_h:
        scores["headings"] = max(0, int(100 * n_heads / min_h)) if min_h > 0 else 100
    else:
        scores["headings"] = max(0, int(100 * max_h / n_heads))

    # Whitespace quality (0-100)
    max_sp = _max_consecutive_spaces(text)
    allowed = expect.get("max_spaces", 3)
    if max_sp <= allowed:
        scores["whitespace"] = 100
    else:
        scores["whitespace"] = max(0, int(100 * allowed / max_sp))

    # Content completeness (0-100)
    phrases = expect.get("key_phrases", [])
    if phrases:
        found, total = _has_phrases(text, phrases)
        scores["content"] = int(100 * found / total)
    else:
        scores["content"] = 100

    # Length check (0-100)
    min_len = expect.get("min_length", 100)
    if len(text) >= min_len:
        scores["length"] = 100
    else:
        scores["length"] = int(100 * len(text) / min_len)

    # Overall
    weights = {"tables": 30, "headings": 20, "whitespace": 15, "content": 25, "length": 10}
    total_w = sum(weights.values())
    scores["overall"] = sum(scores[k] * weights[k] for k in weights) // total_w

    scores["_detail"] = {
        "tables_found": n_tables,
        "headings_found": n_heads,
        "max_spaces": max_sp,
        "length": len(text),
    }

    return scores


# === Document expectations ===

BENCHMARKS = [
    {
        "name": "tesla.pdf",
        "path": "TEST_DOC/tesla.pdf",
        "parser": parser_pdf.parse,
        "expect": {
            "min_tables": 2,
            "max_tables": 5,
            "min_headings": 3,
            "max_headings": 15,
            "max_spaces": 3,
            "min_length": 3000,
            "key_phrases": [
                "Tesla",
                "차량 등록",
                "보험가입증명서",
                "모바일 인도 수락",
                "주민등록등본",
            ],
        },
    },
    {
        "name": "FP8_paper.pdf",
        "path": "TEST_DOC/2209.05433v2.pdf",
        "parser": parser_pdf.parse,
        "expect": {
            "min_tables": 3,
            "max_tables": 10,
            "min_headings": 5,
            "max_headings": 20,
            "max_spaces": 3,
            "min_length": 20000,
            "key_phrases": [
                "FP8",
                "E4M3",
                "E5M2",
                "deep learning",
                "Table 1",
                "Image Classification",
            ],
        },
    },
    {
        "name": "credit_card.pdf",
        "path": "TEST_DOC/0152023081705.pdf",
        "parser": parser_pdf.parse,
        "expect": {
            "min_tables": 1,
            "max_tables": 10,
            "min_headings": 3,
            "max_headings": 25,
            "max_spaces": 3,
            "min_length": 10000,
            "key_phrases": [
                "신용카드",
                "연회비",
                "마일리지",
                "삼성카드",
            ],
        },
    },
    {
        "name": "On_Device_AI.pptx",
        "path": "TEST_DOC/On_Device_AI.pptx",
        "parser": parser_pptx.parse,
        "expect": {
            "min_tables": 1,
            "max_tables": 5,
            "min_headings": 3,
            "max_headings": 10,
            "max_spaces": 3,
            "min_length": 2000,
            "key_phrases": [
                "On-Device",
                "SK",
                "Raspberry-Pi",
                "TensorFlow",
                "경량",
            ],
        },
    },
    {
        "name": "3GPP_6G.xlsx",
        "path": "TEST_DOC/TDoc_List_Meeting_-3GPP workshop on 6G.xlsx",
        "parser": parser_xlsx.parse,
        "expect": {
            "min_tables": 1,
            "max_tables": 5,
            "min_headings": 1,
            "max_headings": 10,
            "max_spaces": 3,
            "min_length": 50000,
            "key_phrases": [
                "TDoc",
                "6G",
            ],
        },
    },
]


def run_benchmark():
    total_overall = 0
    results = []

    for bench in BENCHMARKS:
        path = bench["path"]
        if not Path(path).exists():
            print(f"SKIP {bench['name']}: file not found")
            continue

        text = bench["parser"](path)
        scores = score_document(bench["name"], text, bench["expect"])
        results.append((bench["name"], scores))
        total_overall += scores["overall"]

    print("=" * 70)
    print(f"{'Document':<22} {'Tables':>7} {'Heads':>7} {'WSpace':>7} {'Content':>7} {'Len':>7} {'TOTAL':>7}")
    print("-" * 70)
    for name, s in results:
        d = s["_detail"]
        print(
            f"{name:<22} {s['tables']:>5}({d['tables_found']}) "
            f"{s['headings']:>5}({d['headings_found']}) "
            f"{s['whitespace']:>5}({d['max_spaces']}) "
            f"{s['content']:>7} {s['length']:>7} {s['overall']:>7}"
        )
    print("-" * 70)
    avg = total_overall // len(results) if results else 0
    print(f"{'AVERAGE':>59} {avg:>7}")
    print("=" * 70)
    return avg


if __name__ == "__main__":
    run_benchmark()
