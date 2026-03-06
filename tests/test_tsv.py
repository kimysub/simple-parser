"""Tests for the TSV parser."""

from pathlib import Path

from simple_parser import parser_tsv

FIXTURES = Path(__file__).parent / "fixtures"


def test_headers():
    result = parser_tsv.parse(str(FIXTURES / "sample.tsv"))
    assert "Name" in result
    assert "Age" in result


def test_data_row():
    result = parser_tsv.parse(str(FIXTURES / "sample.tsv"))
    assert "Alice" in result
    assert "30" in result


def test_markdown_table_format():
    result = parser_tsv.parse(str(FIXTURES / "sample.tsv"))
    assert "| Name | Age |" in result
    assert "| --- | --- |" in result


def test_multiple_rows():
    result = parser_tsv.parse(str(FIXTURES / "sample.tsv"))
    assert "Bob" in result
    assert "25" in result
