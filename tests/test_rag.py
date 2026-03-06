"""Tests for the RAG post-processor."""

from simple_parser.rag import clean_for_rag


def test_strips_heading_markers():
    assert clean_for_rag("# Title") == "Title"
    assert clean_for_rag("## Subtitle") == "Subtitle"
    assert clean_for_rag("### Deep") == "Deep"


def test_strips_bold():
    assert clean_for_rag("**bold text**") == "bold text"


def test_strips_italic():
    assert clean_for_rag("*italic text*") == "italic text"


def test_strips_inline_code():
    assert clean_for_rag("`code`") == "code"


def test_converts_links():
    result = clean_for_rag("[click](https://example.com)")
    assert result == "click (https://example.com)"


def test_converts_images():
    result = clean_for_rag("![photo](pic.png)")
    assert result == "photo"


def test_removes_horizontal_rules():
    result = clean_for_rag("text\n\n---\n\nmore text")
    assert "---" not in result
    assert "text" in result
    assert "more text" in result


def test_linearizes_table():
    table = "| Name | Age |\n| --- | --- |\n| Alice | 30 |"
    result = clean_for_rag(table)
    assert "Name: Alice" in result
    assert "Age: 30" in result
    assert "|" not in result
    assert "---" not in result


def test_linearizes_multi_row_table():
    table = "| Name | Age |\n| --- | --- |\n| Alice | 30 |\n| Bob | 25 |"
    result = clean_for_rag(table)
    assert "Name: Alice; Age: 30" in result
    assert "Name: Bob; Age: 25" in result


def test_strips_slide_prefix():
    result = clean_for_rag("## Slide 1: Intro")
    assert result == "Intro"
    assert "Slide 1" not in result


def test_preserves_plain_text():
    text = "Normal paragraph text."
    assert clean_for_rag(text) == text


def test_preserves_list_markers():
    text = "- item one\n- item two"
    result = clean_for_rag(text)
    assert "- item one" in result
    assert "- item two" in result


def test_preserves_code_block_content():
    text = "```\nprint('hello')\n```"
    result = clean_for_rag(text)
    assert "print('hello')" in result
    assert "```" not in result


def test_collapses_excess_newlines():
    text = "first\n\n\n\n\nsecond"
    result = clean_for_rag(text)
    assert "\n\n\n" not in result
    assert "first" in result
    assert "second" in result


def test_full_docx_output():
    """Realistic DOCX parser output."""
    md = (
        "# Test Heading\n\n"
        "Normal paragraph.\n\n"
        "**Bold text** and *italic text*\n\n"
        "| A | B |\n"
        "| --- | --- |\n"
        "| 1 | 2 |\n\n"
        "- Bullet one\n\n"
        "- Bullet two"
    )
    result = clean_for_rag(md)
    assert "Test Heading" in result
    assert "#" not in result
    assert "**" not in result
    assert "*" not in result.replace("Bullet", "")  # no stray asterisks
    assert "A: 1; B: 2" in result
    assert "|" not in result


def test_full_xlsx_output():
    """Realistic XLSX parser output."""
    md = "## Sheet: Data\n\n| Name | Age |\n| --- | --- |\n| Alice | 30 |"
    result = clean_for_rag(md)
    assert "Sheet: Data" in result
    assert "Name: Alice; Age: 30" in result
    assert "#" not in result
    assert "|" not in result
