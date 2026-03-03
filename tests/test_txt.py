"""Tests for the TXT parser."""

from pathlib import Path

from simple_parser.parser_txt import parse

FIXTURES = Path(__file__).parent / "fixtures"


def test_utf8():
    result = parse(str(FIXTURES / "sample.txt"))
    assert "Hello world" in result
    assert "Second line." in result


def test_utf8_bom(tmp_path):
    f = tmp_path / "bom.txt"
    f.write_bytes(b"\xef\xbb\xbf" + "BOM content".encode("utf-8"))
    result = parse(str(f))
    assert result == "BOM content"


def test_utf16le_bom(tmp_path):
    f = tmp_path / "u16le.txt"
    f.write_bytes(b"\xff\xfe" + "UTF-16LE text".encode("utf-16-le"))
    result = parse(str(f))
    assert result == "UTF-16LE text"


def test_utf16be_bom(tmp_path):
    f = tmp_path / "u16be.txt"
    f.write_bytes(b"\xfe\xff" + "UTF-16BE text".encode("utf-16-be"))
    result = parse(str(f))
    assert result == "UTF-16BE text"


def test_latin1_fallback(tmp_path):
    f = tmp_path / "latin1.txt"
    f.write_bytes("café résumé".encode("latin-1"))
    result = parse(str(f))
    assert "caf" in result
    assert "sum" in result
