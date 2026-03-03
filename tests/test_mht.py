"""Tests for the MHT parser."""

from pathlib import Path

from simple_parser.parser_mht import parse

FIXTURES = Path(__file__).parent / "fixtures"


def test_extracts_text():
    result = parse(str(FIXTURES / "sample.mht"))
    assert "Hello from MHT" in result


def test_strips_html_tags():
    result = parse(str(FIXTURES / "sample.mht"))
    assert "<p>" not in result
    assert "<html>" not in result


def test_strips_body_tags():
    result = parse(str(FIXTURES / "sample.mht"))
    assert "<body>" not in result
