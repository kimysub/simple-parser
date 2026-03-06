"""Tests for the INI parser."""

from pathlib import Path

from simple_parser import parser_ini

FIXTURES = Path(__file__).parent / "fixtures"


def test_contains_content():
    result = parser_ini.parse(str(FIXTURES / "sample.ini"))
    assert "[server]" in result


def test_wrapped_in_code_block():
    result = parser_ini.parse(str(FIXTURES / "sample.ini"))
    assert result.startswith("```ini\n")
    assert result.endswith("\n```")
