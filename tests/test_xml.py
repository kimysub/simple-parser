"""Tests for the XML parser."""

from pathlib import Path

from simple_parser import parser_xml

FIXTURES = Path(__file__).parent / "fixtures"


def test_contains_content():
    result = parser_xml.parse(str(FIXTURES / "sample.xml"))
    assert "<root>" in result


def test_wrapped_in_code_block():
    result = parser_xml.parse(str(FIXTURES / "sample.xml"))
    assert result.startswith("```xml\n")
    assert result.endswith("\n```")
