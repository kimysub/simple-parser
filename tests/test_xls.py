"""Tests for the XLS parser."""

from pathlib import Path

from simple_parser.parser_xls import parse

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_sheet_name():
    result = parse(str(FIXTURES / "sample.xls"))
    assert "## Sheet: Data" in result


def test_parse_headers():
    result = parse(str(FIXTURES / "sample.xls"))
    assert "| Name | Age |" in result


def test_parse_data_row():
    result = parse(str(FIXTURES / "sample.xls"))
    assert "| Alice | 30 |" in result


def test_parse_table_separator():
    result = parse(str(FIXTURES / "sample.xls"))
    assert "| --- | --- |" in result
