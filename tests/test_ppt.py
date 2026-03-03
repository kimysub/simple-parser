"""Tests for the PPT parser (requires LibreOffice)."""

import shutil

import pytest

pytestmark = pytest.mark.skipif(
    not shutil.which("libreoffice"),
    reason="LibreOffice not installed",
)

from pathlib import Path

from simple_parser.parser_ppt import parse

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def ppt_path():
    path = FIXTURES / "sample.ppt"
    if not path.exists():
        pytest.skip("sample.ppt fixture not available")
    return path


def test_returns_markdown(ppt_path):
    result = parse(str(ppt_path))
    assert len(result) > 0


def test_contains_slide_content(ppt_path):
    result = parse(str(ppt_path))
    assert "Slide" in result


def test_extracts_text(ppt_path):
    result = parse(str(ppt_path))
    assert "Intro" in result or "Details" in result or "Body" in result
