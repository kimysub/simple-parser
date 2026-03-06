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
    f = tmp_path / "test.xyz"
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


def test_txt_stdout():
    result = run_cli(str(FIXTURES / "sample.txt"))
    assert result.returncode == 0
    assert "Hello world" in result.stdout


def test_eml_stdout():
    result = run_cli(str(FIXTURES / "sample.eml"))
    assert result.returncode == 0
    assert "Test Subject" in result.stdout


def test_mht_stdout():
    result = run_cli(str(FIXTURES / "sample.mht"))
    assert result.returncode == 0
    assert "Hello from MHT" in result.stdout


def test_md_stdout():
    result = run_cli(str(FIXTURES / "sample.md"))
    assert result.returncode == 0
    assert "# Heading" in result.stdout


def test_xls_stdout():
    result = run_cli(str(FIXTURES / "sample.xls"))
    assert result.returncode == 0
    assert "Sheet: Data" in result.stdout


def test_json_stdout():
    result = run_cli(str(FIXTURES / "sample.json"))
    assert result.returncode == 0
    assert "Alice" in result.stdout


def test_yaml_stdout():
    result = run_cli(str(FIXTURES / "sample.yaml"))
    assert result.returncode == 0
    assert "name: Alice" in result.stdout


def test_xml_stdout():
    result = run_cli(str(FIXTURES / "sample.xml"))
    assert result.returncode == 0
    assert "<root>" in result.stdout


def test_csv_stdout():
    result = run_cli(str(FIXTURES / "sample.csv"))
    assert result.returncode == 0
    assert "Alice" in result.stdout


def test_tsv_stdout():
    result = run_cli(str(FIXTURES / "sample.tsv"))
    assert result.returncode == 0
    assert "Alice" in result.stdout


def test_toml_stdout():
    result = run_cli(str(FIXTURES / "sample.toml"))
    assert result.returncode == 0
    assert "[server]" in result.stdout


def test_ini_stdout():
    result = run_cli(str(FIXTURES / "sample.ini"))
    assert result.returncode == 0
    assert "[server]" in result.stdout


def test_output_flag(tmp_path):
    out = tmp_path / "output.md"
    result = run_cli(str(FIXTURES / "sample.docx"), "-o", str(out))
    assert result.returncode == 0
    content = out.read_text()
    assert "# Test Heading" in content
