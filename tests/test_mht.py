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


def test_converts_html_to_markdown(tmp_path):
    """MHT with rich HTML should produce markdown, not stripped text."""
    mht = tmp_path / "rich.mht"
    mht.write_text(
        "MIME-Version: 1.0\r\n"
        'Content-Type: multipart/related; boundary="b"\r\n'
        "\r\n"
        "--b\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        "\r\n"
        "<html><body><h1>Title</h1><p>A <b>bold</b> word and "
        '<a href="https://example.com">link</a>.</p></body></html>\r\n'
        "--b--\r\n",
        encoding="utf-8",
    )
    result = parse(str(mht))
    assert "# Title" in result
    assert "**bold**" in result
    assert "[link](https://example.com)" in result
