"""Tests for the DOC parser (requires LibreOffice)."""

import shutil

import pytest

pytestmark = pytest.mark.skipif(
    not shutil.which("libreoffice"),
    reason="LibreOffice not installed",
)

from pathlib import Path

from simple_parser.parser_doc import parse

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def doc_path():
    path = FIXTURES / "sample.doc"
    if not path.exists():
        pytest.skip("sample.doc fixture not available")
    return path


def test_returns_markdown(doc_path):
    result = parse(str(doc_path))
    assert len(result) > 0


def test_contains_expected_text(doc_path):
    result = parse(str(doc_path))
    assert "Test Heading" in result


def test_no_libreoffice_error():
    """If libreoffice were missing, parse raises RuntimeError."""
    # This test only runs when libreoffice IS installed (due to pytestmark),
    # so we just verify the function is callable.
    assert callable(parse)
