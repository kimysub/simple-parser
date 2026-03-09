# Simple Parser - Implementation Plan

## Context

**Problem**: CLI tool to parse document files (docx, pptx, xlsx, pdf, xls, doc, ppt, txt, eml, mht/mhtml, md, json, yaml, xml, csv, tsv, toml, ini) into Markdown format.
**Constraints**: XML-based parsing for Office formats (ZIP archives containing XML), no OCR for PDF, prioritize simplicity and speed. Legacy Office formats via LibreOffice headless conversion. Text data formats use stdlib only.

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
    parser_xls.py                   # XLS  -> Markdown (xlrd)
    parser_doc.py                   # DOC  -> Markdown (LibreOffice → DOCX)
    parser_ppt.py                   # PPT  -> Markdown (LibreOffice → PPTX)
    parser_txt.py                   # TXT  -> Markdown (BOM-aware encoding)
    parser_eml.py                   # EML  -> Markdown (email headers + body)
    parser_mht.py                   # MHT  -> Markdown (MIME HTML-to-Markdown)
    parser_md.py                    # MD   -> pass-through
    parser_json.py                  # JSON -> Markdown (pretty-printed code block)
    parser_yaml.py                  # YAML -> Markdown (code block)
    parser_xml.py                   # XML  -> Markdown (code block)
    parser_csv.py                   # CSV  -> Markdown table
    parser_tsv.py                   # TSV  -> Markdown table
    parser_toml.py                  # TOML -> Markdown (code block)
    parser_ini.py                   # INI  -> Markdown (code block)
    rag.py                          # RAG post-processor (clean text for embedding)
  tests/
    __init__.py
    conftest.py                     # Shared fixtures
    fixtures/                       # Sample test files
    test_md.py
    test_docx.py
    test_pptx.py
    test_xlsx.py
    test_pdf.py
    test_xls.py
    test_doc.py
    test_ppt.py
    test_txt.py
    test_eml.py
    test_mht.py
    test_md_parser.py
    test_rag.py
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
| `zipfile`, `xml.etree.ElementTree`, `argparse`, `pathlib`, `re`, `email` | Office XML parsing, CLI, email/MHT parsing | stdlib |
| `pymupdf` (PyMuPDF) | PDF text extraction (no OCR) | external |
| `xlrd` | XLS (BIFF) spreadsheet parsing | external |
| LibreOffice | DOC/PPT → DOCX/PPTX headless conversion | system (optional) |
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
- **Known limitation**: Mathematical equations may render incorrectly (PDFs store equations as positioned glyphs, not semantic math notation)
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

### Phase 9: Expanded File Type Support
- Add 7 new format parsers: XLS (xlrd), DOC/PPT (LibreOffice headless), TXT (BOM-aware), EML (email), MHT/MHTML (MIME HTML), MD (pass-through)
- Register all new parsers in `cli.py` and `api.py` (PARSERS dict + MIME_TO_EXT)
- Add `xlrd>=2.0` dependency, LibreOffice to Dockerfile
- 7 new parser test files + updated CLI/API tests (parametrized for 11 formats)
- DOC/PPT tests skip when LibreOffice is not installed
- **Verify**: `pytest tests/` all green (87 passed, 10 skipped without LibreOffice)

### Phase 10: RAG Post-Processor
- Add `rag.py` module with `clean_for_rag()` function for embedding-optimized text output
- Strip markdown formatting (headings, bold, italic, code markers)
- Linearize tables to key-value rows (`Name: Alice; Age: 30`)
- Strip slide numbering prefixes, horizontal rules, image/link syntax
- Apply automatically in `PUT /process` endpoint (Open WebUI RAG)
- Add `--clean` CLI flag for same behavior
- Add `html_to_md()` to `md.py` for proper HTML-to-Markdown conversion in EML/MHT parsers
- **Verify**: `pytest tests/` all green (116 passed, 10 skipped without LibreOffice)

### Phase 11: Text Data Format Support
- Add 7 new text-based parsers: JSON (pretty-print), YAML, XML, CSV (→ table), TSV (→ table), TOML, INI
- JSON pretty-prints with `json.dumps(indent=2)` and wraps in fenced code block
- CSV/TSV parse with stdlib `csv` module and convert to markdown tables via `md.table()`
- YAML, XML, TOML, INI wrap content in language-tagged fenced code blocks
- Register all parsers in `cli.py` and `api.py` (PARSERS dict + MIME_TO_EXT)
- Extensions: `.json`, `.yaml`, `.yml`, `.xml`, `.csv`, `.tsv`, `.toml`, `.ini`, `.cfg`
- No new external dependencies (stdlib only)
- **Verify**: `pytest tests/` all green (146 passed, 10 skipped without LibreOffice)

### Phase 12: Table Detection & PDF/PPTX Quality Improvements
- PDF table detection:
  - Bordered tables via `page.find_tables()` (PyMuPDF), extracts as markdown tables via `md.table()`
  - Borderless table detection for academic papers (`Table N:` pattern + per-line column grouping)
  - Table caption preservation in output
  - Rectangle overlap check to exclude table regions from regular text extraction (prevents duplication)
- PDF text quality improvements:
  - Smart body size detection: rounds font sizes to integers, uses max of sizes with >5% share AND >200 chars as effective body size
  - Heading threshold: strict `<` boundary (not `<=`) for exact body size exclusion
  - Heading min length (10 chars) to filter short labels
  - Heading max length (200 chars) to filter paragraphs misclassified as headings
  - Ligature normalization (ﬁ→fi, ﬂ→fl, ﬀ→ff, ﬃ→ffi, ﬄ→ffl)
  - Whitespace collapse (multiple spaces → single space)
- PPTX improvements:
  - DrawingML table parsing (`a:tbl` inside `p:graphicFrame`), extracts header + data rows from `a:tr`/`a:tc`
  - Whitespace collapse for split text runs
- Benchmark: `tests/benchmark.py` scoring system (tables 30%, content 25%, headings 20%, whitespace 15%, length 10%) tested against 5 real documents, improved from 83/100 → 100/100 average score
- **Verify**: `pytest tests/` all green (152 passed, 10 skipped without LibreOffice)
