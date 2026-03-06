"""Tests for the CSV parser."""

from pathlib import Path

from simple_parser import parser_csv

FIXTURES = Path(__file__).parent / "fixtures"


def test_headers():
    result = parser_csv.parse(str(FIXTURES / "sample.csv"))
    assert "Name" in result
    assert "Age" in result


def test_data_row():
    result = parser_csv.parse(str(FIXTURES / "sample.csv"))
    assert "Alice" in result
    assert "30" in result


def test_markdown_table_format():
    result = parser_csv.parse(str(FIXTURES / "sample.csv"))
    assert "| Name | Age |" in result
    assert "| --- | --- |" in result
    assert "| Alice | 30 |" in result


def test_multiple_rows():
    result = parser_csv.parse(str(FIXTURES / "sample.csv"))
    assert "Bob" in result
    assert "25" in result
