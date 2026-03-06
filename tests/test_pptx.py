"""Tests for PPTX parser."""

from simple_parser.parser_pptx import parse

FIXTURE = "tests/fixtures/sample.pptx"


def test_parse_slide_titles():
    result = parse(FIXTURE)
    assert "## Slide 1: Intro Slide" in result
    assert "## Slide 2: Details" in result


def test_parse_slide_body():
    result = parse(FIXTURE)
    assert "Body text here." in result
    assert "More details." in result


def test_slide_ordering():
    result = parse(FIXTURE)
    pos1 = result.index("Slide 1")
    pos2 = result.index("Slide 2")
    assert pos1 < pos2


TABLE_FIXTURE = "tests/fixtures/sample_table.pptx"


def test_table_in_slide():
    result = parse(TABLE_FIXTURE)
    assert "| Product | Revenue |" in result
    assert "| --- | --- |" in result


def test_table_data_rows():
    result = parse(TABLE_FIXTURE)
    assert "| Widget A | 50000 |" in result
    assert "| Widget B | 75000 |" in result


def test_table_with_title():
    result = parse(TABLE_FIXTURE)
    assert "Data Slide" in result
