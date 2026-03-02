"""Tests for markdown helpers."""

from simple_parser.md import (
    heading,
    bold,
    italic,
    table,
    escape,
    unordered_list,
    ordered_list,
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
