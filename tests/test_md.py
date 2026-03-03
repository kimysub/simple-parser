"""Tests for markdown helpers."""

from simple_parser.md import (
    heading,
    bold,
    italic,
    table,
    escape,
    unordered_list,
    ordered_list,
    html_to_md,
)


def test_heading_levels():
    assert heading("Title", 1) == "# Title"
    assert heading("Sub", 2) == "## Sub"
    assert heading("Deep", 4) == "#### Deep"


def test_bold():
    assert bold("word") == "**word**"


def test_italic():
    assert italic("word") == "*word*"


def test_table_basic():
    result = table(["A", "B"], [["1", "2"], ["3", "4"]])
    lines = result.split("\n")
    assert lines[0] == "| A | B |"
    assert lines[1] == "| --- | --- |"
    assert lines[2] == "| 1 | 2 |"
    assert lines[3] == "| 3 | 4 |"


def test_table_pads_short_rows():
    result = table(["A", "B", "C"], [["1"]])
    lines = result.split("\n")
    assert lines[2] == "| 1 |  |  |"


def test_escape():
    assert escape("hello") == "hello"
    assert escape("a*b") == "a\\*b"
    assert escape("a_b") == "a\\_b"
    assert escape("[link](url)") == "\\[link\\]\\(url\\)"


def test_unordered_list():
    result = unordered_list(["a", "b", "c"])
    assert result == "- a\n- b\n- c"


def test_ordered_list():
    result = ordered_list(["a", "b", "c"])
    assert result == "1. a\n2. b\n3. c"


def test_html_to_md_heading():
    assert html_to_md("<h1>Title</h1>") == "# Title"
    assert html_to_md("<h2>Sub</h2>") == "## Sub"


def test_html_to_md_bold_italic():
    assert html_to_md("<b>bold</b>") == "**bold**"
    assert html_to_md("<strong>bold</strong>") == "**bold**"
    assert html_to_md("<em>italic</em>") == "*italic*"
    assert html_to_md("<i>italic</i>") == "*italic*"


def test_html_to_md_link():
    result = html_to_md('<a href="https://example.com">click</a>')
    assert result == "[click](https://example.com)"


def test_html_to_md_paragraphs():
    result = html_to_md("<p>First.</p><p>Second.</p>")
    assert "First." in result
    assert "Second." in result
    assert "\n\n" in result


def test_html_to_md_lists():
    result = html_to_md("<ul><li>a</li><li>b</li></ul>")
    assert "- a" in result
    assert "- b" in result

    result = html_to_md("<ol><li>x</li><li>y</li></ol>")
    assert "1. x" in result
    assert "2. y" in result


def test_html_to_md_code():
    assert "`code`" in html_to_md("<code>code</code>")


def test_html_to_md_pre():
    result = html_to_md("<pre>line1\nline2</pre>")
    assert "```" in result
    assert "line1" in result


def test_html_to_md_img():
    result = html_to_md('<img src="pic.png" alt="photo">')
    assert result == "![photo](pic.png)"


def test_html_to_md_strips_unknown_tags():
    result = html_to_md("<span>text</span>")
    assert "text" in result
    assert "<span>" not in result
