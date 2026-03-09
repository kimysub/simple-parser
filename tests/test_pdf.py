"""Tests for PDF parser."""

from simple_parser.parser_pdf import parse

FIXTURE = "tests/fixtures/sample.pdf"


def test_parse_heading():
    result = parse(FIXTURE)
    # "Big Heading" is 24pt vs 12pt body — should be detected as heading
    assert "# Big Heading" in result


def test_parse_body_text():
    result = parse(FIXTURE)
    assert "This is body text on page one." in result


def test_parse_page_separator():
    result = parse(FIXTURE)
    assert "---" in result


def test_parse_second_page():
    result = parse(FIXTURE)
    assert "Page two content here." in result


def test_page_order():
    result = parse(FIXTURE)
    pos1 = result.index("page one")
    pos2 = result.index("Page two")
    assert pos1 < pos2


TABLE_FIXTURE = "tests/fixtures/sample_table.pdf"


def test_table_detection():
    result = parse(TABLE_FIXTURE)
    assert "| Name | Age |" in result
    assert "| --- | --- |" in result


def test_table_data_rows():
    result = parse(TABLE_FIXTURE)
    assert "| Alice | 30 |" in result
    assert "| Bob | 25 |" in result


def test_table_text_not_duplicated():
    """Table text should not appear as both table and free text."""
    result = parse(TABLE_FIXTURE)
    # "Alice" should appear only in the table, not duplicated as free text
    assert result.count("Alice") == 1
