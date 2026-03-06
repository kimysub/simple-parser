"""Tests for the FastAPI endpoints."""

import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from simple_parser.api import app

_has_libreoffice = bool(shutil.which("libreoffice"))

FIXTURES_DIR = Path(__file__).parent / "fixtures"

client = TestClient(app)

EXPECTED_KEYS = {"filename", "format", "markdown", "output_file", "parsed_at"}


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


_ALL_FORMATS = [
    "sample.docx", "sample.pptx", "sample.xlsx", "sample.pdf",
    "sample.txt", "sample.eml", "sample.mht", "sample.md", "sample.xls",
    "sample.json", "sample.yaml", "sample.xml", "sample.csv",
    "sample.tsv", "sample.toml", "sample.ini",
    pytest.param("sample.doc", marks=pytest.mark.skipif(
        not _has_libreoffice or not (FIXTURES_DIR / "sample.doc").exists(),
        reason="LibreOffice or fixture not available",
    )),
    pytest.param("sample.ppt", marks=pytest.mark.skipif(
        not _has_libreoffice or not (FIXTURES_DIR / "sample.ppt").exists(),
        reason="LibreOffice or fixture not available",
    )),
]


@pytest.mark.parametrize("name", _ALL_FORMATS)
def test_parse_supported_formats(name):
    path = FIXTURES_DIR / name
    with open(path, "rb") as f:
        resp = client.post("/parse", files={"file": (name, f)})
    assert resp.status_code == 200
    data = resp.json()
    assert set(data.keys()) == EXPECTED_KEYS
    assert data["filename"] == name
    assert data["format"] == Path(name).suffix
    assert len(data["markdown"]) > 0
    assert data["output_file"].endswith(".md")


def test_unsupported_format():
    resp = client.post("/parse", files={"file": ("test.xyz", b"hello")})
    assert resp.status_code == 400
    assert "Unsupported format" in resp.json()["detail"]


def test_corrupt_file():
    resp = client.post("/parse", files={"file": ("bad.docx", b"not a zip")})
    assert resp.status_code == 400
    assert "Corrupt" in resp.json()["detail"]


def test_missing_file_returns_422():
    resp = client.post("/parse")
    assert resp.status_code == 422


# --- PUT /process (Open WebUI compatible) ---

PROCESS_EXPECTED_KEYS = {"page_content", "metadata"}


@pytest.mark.parametrize("name", _ALL_FORMATS)
def test_process_supported_formats(name):
    path = FIXTURES_DIR / name
    resp = client.put(
        "/process",
        content=path.read_bytes(),
        headers={"X-Filename": name},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert set(data.keys()) == PROCESS_EXPECTED_KEYS
    assert len(data["page_content"]) > 0
    assert data["metadata"]["source"] == name
    assert data["metadata"]["format"] == Path(name).suffix


def test_process_returns_rag_clean_text():
    """PUT /process should return RAG-optimized clean text, not raw markdown."""
    path = FIXTURES_DIR / "sample.docx"
    resp = client.put(
        "/process",
        content=path.read_bytes(),
        headers={"X-Filename": "sample.docx"},
    )
    assert resp.status_code == 200
    content = resp.json()["page_content"]
    # Should not contain markdown formatting
    assert "# " not in content
    assert "**" not in content
    assert "| --- |" not in content
    # Should contain the actual text
    assert "Test Heading" in content


def test_process_xlsx_linearizes_tables():
    """PUT /process should linearize tables for RAG."""
    path = FIXTURES_DIR / "sample.xlsx"
    resp = client.put(
        "/process",
        content=path.read_bytes(),
        headers={"X-Filename": "sample.xlsx"},
    )
    assert resp.status_code == 200
    content = resp.json()["page_content"]
    assert "Name: Alice" in content
    assert "|" not in content


def test_process_mime_fallback():
    path = FIXTURES_DIR / "sample.docx"
    resp = client.put(
        "/process",
        content=path.read_bytes(),
        headers={
            "Content-Type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        },
    )
    assert resp.status_code == 200
    assert len(resp.json()["page_content"]) > 0


def test_process_unsupported():
    resp = client.put(
        "/process",
        content=b"hello",
        headers={"X-Filename": "test.xyz"},
    )
    assert resp.status_code == 400
    assert "Unsupported format" in resp.json()["detail"]


def test_process_empty_body():
    resp = client.put("/process", content=b"")
    assert resp.status_code == 400
    assert "Empty" in resp.json()["detail"]


def test_process_corrupt_file():
    resp = client.put(
        "/process",
        content=b"not a zip",
        headers={"X-Filename": "bad.docx"},
    )
    assert resp.status_code == 400
    assert "Corrupt" in resp.json()["detail"]


def test_process_api_key_valid(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")
    path = FIXTURES_DIR / "sample.docx"
    resp = client.put(
        "/process",
        content=path.read_bytes(),
        headers={"X-Filename": "sample.docx", "Authorization": "Bearer test-key"},
    )
    assert resp.status_code == 200
    assert len(resp.json()["page_content"]) > 0


def test_process_api_key_invalid(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")
    resp = client.put(
        "/process",
        content=b"data",
        headers={"X-Filename": "sample.docx", "Authorization": "Bearer wrong-key"},
    )
    assert resp.status_code == 401
    assert "Invalid" in resp.json()["detail"]
