"""Tests for XLSX parser."""

from simple_parser.parser_xlsx import parse, _col_to_index

FIXTURE = "tests/fixtures/sample.xlsx"


def test_col_to_index():
    assert _col_to_index("A") == 0
    assert _col_to_index("B") == 1
    assert _col_to_index("Z") == 25
    assert _col_to_index("AA") == 26
    assert _col_to_index("AB") == 27


def test_parse_sheet_name():
    result = parse(FIXTURE)
    assert "## Sheet: Data" in result


def test_parse_headers():
    result = parse(FIXTURE)
    assert "| Name | Age |" in result


def test_parse_data_row():
    result = parse(FIXTURE)
    assert "| Alice | 30 |" in result


def test_parse_table_separator():
    result = parse(FIXTURE)
    assert "| --- | --- |" in result
