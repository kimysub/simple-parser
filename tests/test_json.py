"""Tests for the JSON parser."""

from pathlib import Path

from simple_parser import parser_json

FIXTURES = Path(__file__).parent / "fixtures"


def test_pretty_prints():
    result = parser_json.parse(str(FIXTURES / "sample.json"))
    assert '"name": "Alice"' in result


def test_wrapped_in_code_block():
    result = parser_json.parse(str(FIXTURES / "sample.json"))
    assert result.startswith("```json\n")
    assert result.endswith("\n```")


def test_indent():
    result = parser_json.parse(str(FIXTURES / "sample.json"))
    # json.dumps(indent=2) produces indented output
    assert "  " in result
