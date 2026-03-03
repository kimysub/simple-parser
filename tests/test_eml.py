"""Tests for the EML parser."""

from pathlib import Path

from simple_parser.parser_eml import parse

FIXTURES = Path(__file__).parent / "fixtures"


def test_subject_heading():
    result = parse(str(FIXTURES / "sample.eml"))
    assert "# Test Subject" in result


def test_from_header():
    result = parse(str(FIXTURES / "sample.eml"))
    assert "sender@example.com" in result


def test_date_header():
    result = parse(str(FIXTURES / "sample.eml"))
    assert "Mon, 01 Jan 2024" in result


def test_body_text():
    result = parse(str(FIXTURES / "sample.eml"))
    assert "This is the email body." in result


def test_html_body_converted_to_markdown(tmp_path):
    """When body is HTML-only, it should be converted to markdown."""
    eml = tmp_path / "html.eml"
    eml.write_text(
        "From: a@b.com\r\n"
        "Subject: HTML Email\r\n"
        "MIME-Version: 1.0\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        "\r\n"
        "<html><body><h2>Section</h2><p>A <b>bold</b> word.</p></body></html>\r\n",
        encoding="utf-8",
    )
    result = parse(str(eml))
    assert "# HTML Email" in result
    assert "## Section" in result
    assert "**bold**" in result
