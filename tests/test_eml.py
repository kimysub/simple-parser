"""Tests for the EML parser."""

from pathlib import Path

from simple_parser.parser_eml import parse

FIXTURES = Path(__file__).parent / "fixtures"


def test_subject_heading():
    result = parse(str(FIXTURES / "sample.eml"))
    assert "# Test Subject" in result


def test_from_header():
    result = parse(str(FIXTURES / "sample.eml"))
    assert "sender@example.com" in result


def test_date_header():
    result = parse(str(FIXTURES / "sample.eml"))
    assert "Mon, 01 Jan 2024" in result


def test_body_text():
    result = parse(str(FIXTURES / "sample.eml"))
    assert "This is the email body." in result
