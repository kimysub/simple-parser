# Simple Parser - Implementation Plan

## Context

**Problem**: CLI tool to parse document files (docx, pptx, xlsx, pdf) into Markdown format.
**Constraints**: XML-based parsing for Office formats (ZIP archives containing XML), no OCR for PDF, prioritize simplicity and speed.

---

## Architecture

**Language**: Python 3.10+
**Approach**: Office formats (docx/pptx/xlsx) are ZIP files containing XML. Parse with stdlib `zipfile` + `xml.etree.ElementTree`. PDF uses PyMuPDF (`fitz`) for non-OCR text extraction.

### Project Structure
```
simple-parser/
  pyproject.toml                    # Dependencies, CLI entry point
  src/simple_parser/
    __init__.py                     # Package init
    cli.py                          # CLI (argparse), format dispatch
    md.py                           # Shared markdown output helpers
    parser_docx.py                  # DOCX -> Markdown
    parser_pptx.py                  # PPTX -> Markdown
    parser_xlsx.py                  # XLSX -> Markdown
    parser_pdf.py                   # PDF  -> Markdown
  tests/
    __init__.py
    conftest.py                     # Shared fixtures
    fixtures/                       # Sample test files
    test_md.py
    test_docx.py
    test_pptx.py
    test_xlsx.py
    test_pdf.py
    test_cli.py
    test_api.py
  Dockerfile
  .dockerignore
  docker-compose.yml
  output/                           # Parsed markdown output (host-mounted)
```

### Dependencies
| Dependency | Purpose | Type |
|---|---|---|
| `zipfile`, `xml.etree.ElementTree`, `argparse`, `pathlib`, `re` | Office XML parsing, CLI | stdlib |
| `pymupdf` (PyMuPDF) | PDF text extraction (no OCR) | external |
| `fastapi`, `uvicorn`, `python-multipart` | Web API server | optional (`[api]`) |
| `pytest`, `httpx`, `ruff` | Testing, linting | optional (`[dev]`) |

### Uniform Parser Interface
Each parser exposes: `def parse(path: str) -> str` returning a Markdown string.

---

## Phases

### Phase 0: Project Scaffolding
- Create `pyproject.toml` with dependencies and `simple-parser` CLI entry point
- Create `src/simple_parser/__init__.py`, `cli.py` (argparse + dispatch by extension)
- Stub all parser modules with `NotImplementedError`
- Create `tests/` skeleton
- **Verify**: `simple-parser --help` prints usage

### Phase 1: Markdown Utilities (`md.py`)
- `heading(text, level)`, `bold(text)`, `italic(text)`
- `table(headers, rows)` - GFM pipe table
- `escape(text)` - escape markdown special chars
- `unordered_list(items)`, `ordered_list(items)`
- **Verify**: `pytest tests/test_md.py` passes

### Phase 2: DOCX Parser
- Unzip → parse `word/document.xml`
- Extract: headings (`w:pStyle`), paragraphs (`w:p`), bold/italic runs (`w:rPr`), tables (`w:tbl`), lists (`w:numPr` + `word/numbering.xml`)
- OOXML namespace: `w = http://schemas.openxmlformats.org/wordprocessingml/2006/main`
- **Verify**: `pytest tests/test_docx.py` passes

### Phase 3: PPTX Parser
- Unzip → parse `ppt/slides/slide*.xml` (sorted numerically)
- Extract: slide titles (`p:ph type="title"`), text shapes (`a:p/a:r/a:t`)
- Output: `## Slide N: <title>` + body text per slide
- **Verify**: `pytest tests/test_pptx.py` passes

### Phase 4: XLSX Parser
- Unzip → parse `xl/sharedStrings.xml` (string index), `xl/workbook.xml` (sheet names), `xl/worksheets/sheet*.xml` (cell data)
- Cell reference parsing (A1→col 0, row 0), shared string lookup (`t="s"`), number values
- Each sheet → `## Sheet: <name>` + markdown table
- **Verify**: `pytest tests/test_xlsx.py` passes

### Phase 5: PDF Parser
- Use `fitz.open()` → `page.get_text("dict")` for text extraction
- Heading detection via font-size heuristic (larger than modal body size → heading)
- Pages separated by `---`
- **Verify**: `pytest tests/test_pdf.py` passes

### Phase 6: CLI Integration & End-to-End
- Error handling: file not found, unsupported format, corrupt file (`BadZipFile`, fitz exceptions)
- Output to stdout (default) or file (`-o` flag)
- End-to-end tests in `test_cli.py`
- **Verify**: `pytest tests/` all green

### Phase 7: API & Docker
- Add optional dependency groups: `[api]` (fastapi, uvicorn, python-multipart) and `[dev]` (pytest, httpx, ruff)
- Create `api.py` — FastAPI app with `GET /health` and `POST /parse` (file upload, auto-detect format by extension)
- Parsed markdown auto-saved to output directory (`OUTPUT_DIR` env var, defaults to `./output`)
- Error handling: unsupported format → 400, corrupt file → 400, parse failure → 500, missing file → 422
- API tests with FastAPI `TestClient` in `test_api.py`
- `Dockerfile` (python:3.10-slim), `.dockerignore`, `docker-compose.yml` (dev mode with source + output volume mounts, `--reload`)
- **Verify**: `pytest tests/` all green, `docker compose up` + `curl /health` works, parsed files in `./output/`

### Phase 8: Open WebUI Integration
- Add `PUT /process` endpoint — Open WebUI compatible external document loader
- Accept raw file bytes via `request.body()`, determine format from `X-Filename` header or `Content-Type` MIME fallback
- Optional API key authentication via `API_KEY` env var + `Authorization: Bearer` header
- Return `{"page_content": str, "metadata": dict}` response format
- Add `MIME_TO_EXT` mapping for Content-Type → extension fallback
- Add `open-webui` service to `docker-compose.yml` with `CONTENT_EXTRACTION_ENGINE=external`
- 10 new tests in `test_api.py` (4 parametrized format tests + 6 specific tests)
- **Verify**: `pytest tests/` all green (54 tests), `docker compose up` starts both services
