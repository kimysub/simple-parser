"""Tests for PPTX parser."""

from simple_parser.parser_pptx import parse

FIXTURE = "tests/fixtures/sample.pptx"


def test_parse_slide_titles():
    result = parse(FIXTURE)
    assert "## Slide 1: Intro Slide" in result
    assert "## Slide 2: Details" in result


def test_parse_slide_body():
    result = parse(FIXTURE)
    assert "Body text here." in result
    assert "More details." in result


def test_slide_ordering():
    result = parse(FIXTURE)
    pos1 = result.index("Slide 1")
    pos2 = result.index("Slide 2")
    assert pos1 < pos2
