"""Tests for the TOML parser."""

from pathlib import Path

from simple_parser import parser_toml

FIXTURES = Path(__file__).parent / "fixtures"


def test_contains_content():
    result = parser_toml.parse(str(FIXTURES / "sample.toml"))
    assert "[server]" in result


def test_wrapped_in_code_block():
    result = parser_toml.parse(str(FIXTURES / "sample.toml"))
    assert result.startswith("```toml\n")
    assert result.endswith("\n```")
