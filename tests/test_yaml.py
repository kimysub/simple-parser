"""Tests for the YAML parser."""

from pathlib import Path

from simple_parser import parser_yaml

FIXTURES = Path(__file__).parent / "fixtures"


def test_contains_content():
    result = parser_yaml.parse(str(FIXTURES / "sample.yaml"))
    assert "name: Alice" in result


def test_wrapped_in_code_block():
    result = parser_yaml.parse(str(FIXTURES / "sample.yaml"))
    assert result.startswith("```yaml\n")
    assert result.endswith("\n```")
