"""Tests for the MD parser (pass-through)."""

from pathlib import Path

from simple_parser.parser_md import parse

FIXTURES = Path(__file__).parent / "fixtures"


def test_returns_content():
    result = parse(str(FIXTURES / "sample.md"))
    assert "# Heading" in result
    assert "Paragraph text." in result


def test_passthrough_identity():
    path = FIXTURES / "sample.md"
    expected = path.read_text(encoding="utf-8")
    result = parse(str(path))
    assert result == expected
