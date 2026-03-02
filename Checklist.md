# Simple Parser - Phase Checklist

| Phase | Description | Tests | Status |
|---|---|---|---|
| Phase 0 | Project scaffolding (`pyproject.toml`, package structure, CLI stub) | `simple-parser --help` | PASS |
| Phase 1 | Markdown utilities (`md.py`: heading, bold, italic, table, escape, lists) | 8 tests in `test_md.py` | PASS |
| Phase 2 | DOCX parser (headings, paragraphs, bold/italic, tables, bullet/numbered lists) | 6 tests in `test_docx.py` | PASS |
| Phase 3 | PPTX parser (slide titles, body text, slide ordering) | 3 tests in `test_pptx.py` | PASS |
| Phase 4 | XLSX parser (shared strings, sheet names, cell parsing, markdown tables) | 5 tests in `test_xlsx.py` | PASS |
| Phase 5 | PDF parser (PyMuPDF text extraction, font-size heading heuristic, page separators) | 5 tests in `test_pdf.py` | PASS |
| Phase 6 | CLI integration & E2E (error handling, `-o` flag, all format dispatch) | 9 tests in `test_cli.py` | PASS |
| Phase 7 | API & Docker (FastAPI endpoints, Dockerfile, docker-compose) | 8 tests in `test_api.py` | PASS |
| Phase 8 | Open WebUI integration (`PUT /process`, API key auth, MIME fallback) | 10 tests in `test_api.py` | PASS |

**Total: 54 tests, 0 failures**

### Verification Commands
```bash
# Run all tests
python -m pytest tests/ -v

# Lint
ruff check src/ tests/

# Single phase verification
python -m pytest tests/test_md.py -v      # Phase 1
python -m pytest tests/test_docx.py -v    # Phase 2
python -m pytest tests/test_pptx.py -v    # Phase 3
python -m pytest tests/test_xlsx.py -v    # Phase 4
python -m pytest tests/test_pdf.py -v     # Phase 5
python -m pytest tests/test_cli.py -v     # Phase 6
python -m pytest tests/test_api.py -v     # Phase 7 & 8
```
