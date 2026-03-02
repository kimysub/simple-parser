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
