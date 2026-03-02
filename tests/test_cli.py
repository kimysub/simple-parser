"""End-to-end tests for the CLI."""

import subprocess
import sys
from pathlib import Path


FIXTURES = Path("tests/fixtures")


def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "simple_parser.cli", *args],
        capture_output=True,
        text=True,
    )


def test_help():
    result = run_cli("--help")
    assert result.returncode == 0
    assert "simple-parser" in result.stdout


def test_file_not_found():
    result = run_cli("nonexistent.docx")
    assert result.returncode == 1
    assert "file not found" in result.stderr


def test_unsupported_format(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("hello")
    result = run_cli(str(f))
    assert result.returncode == 1
    assert "unsupported format" in result.stderr


def test_corrupt_file(tmp_path):
    f = tmp_path / "bad.docx"
    f.write_text("not a zip file")
    result = run_cli(str(f))
    assert result.returncode == 1
    assert "Error" in result.stderr


def test_docx_stdout():
    result = run_cli(str(FIXTURES / "sample.docx"))
    assert result.returncode == 0
    assert "# Test Heading" in result.stdout


def test_pptx_stdout():
    result = run_cli(str(FIXTURES / "sample.pptx"))
    assert result.returncode == 0
    assert "Slide 1" in result.stdout


def test_xlsx_stdout():
    result = run_cli(str(FIXTURES / "sample.xlsx"))
    assert result.returncode == 0
    assert "Sheet: Data" in result.stdout


def test_pdf_stdout():
    result = run_cli(str(FIXTURES / "sample.pdf"))
    assert result.returncode == 0
    assert "Big Heading" in result.stdout


def test_output_flag(tmp_path):
    out = tmp_path / "output.md"
    result = run_cli(str(FIXTURES / "sample.docx"), "-o", str(out))
    assert result.returncode == 0
    content = out.read_text()
    assert "# Test Heading" in content
