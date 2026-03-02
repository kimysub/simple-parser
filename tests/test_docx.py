"""Tests for DOCX parser."""

from simple_parser.parser_docx import parse

FIXTURE = "tests/fixtures/sample.docx"


def test_parse_heading():
    result = parse(FIXTURE)
    assert "# Test Heading" in result


def test_parse_paragraph():
    result = parse(FIXTURE)
    assert "Normal paragraph." in result


def test_parse_bold_italic():
    result = parse(FIXTURE)
    assert "**Bold text**" in result
    assert "*italic text*" in result


def test_parse_table():
    result = parse(FIXTURE)
    assert "| A | B |" in result
    assert "| 1 | 2 |" in result


def test_parse_bullet_list():
    result = parse(FIXTURE)
    assert "- Bullet one" in result
    assert "- Bullet two" in result


def test_parse_numbered_list():
    result = parse(FIXTURE)
    assert "1. First item" in result
    assert "2. Second item" in result
