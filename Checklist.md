# Simple Parser - Phase Checklist

| Phase | Description | Tests | Status |
|---|---|---|---|
| Phase 0 | Project scaffolding (`pyproject.toml`, package structure, CLI stub) | `simple-parser --help` | PASS |
| Phase 1 | Markdown utilities (`md.py`: heading, bold, italic, table, escape, lists, html_to_md) | 17 tests in `test_md.py` | PASS |
| Phase 2 | DOCX parser (headings, paragraphs, bold/italic, tables, bullet/numbered lists) | 6 tests in `test_docx.py` | PASS |
| Phase 3 | PPTX parser (slide titles, body text, slide ordering) | 3 tests in `test_pptx.py` | PASS |
| Phase 4 | XLSX parser (shared strings, sheet names, cell parsing, markdown tables) | 5 tests in `test_xlsx.py` | PASS |
| Phase 5 | PDF parser (PyMuPDF text extraction, font-size heading heuristic, page separators). ⚠️ Math equations may render incorrectly (known limitation) | 5 tests in `test_pdf.py` | PASS |
| Phase 6 | CLI integration & E2E (error handling, `-o` flag, `--clean` flag, all format dispatch) | 14 tests in `test_cli.py` | PASS |
| Phase 7 | API & Docker (FastAPI endpoints, Dockerfile, docker-compose) | 8 tests in `test_api.py` | PASS |
| Phase 8 | Open WebUI integration (`PUT /process`, API key auth, MIME fallback) | 10 tests in `test_api.py` | PASS |
| Phase 9 | Expanded file type support (xls, doc, ppt, txt, eml, mht, md) | 4 `test_xls` + 3 `test_doc` + 3 `test_ppt` + 5 `test_txt` + 5 `test_eml` + 4 `test_mht` + 2 `test_md_parser` + updated CLI/API | PASS |
| Phase 10 | RAG post-processor + HTML-to-Markdown converter | 16 `test_rag` + 9 `test_md` html_to_md + 2 API RAG tests | PASS |
| Phase 11 | Text data formats (json, yaml, xml, csv, tsv, toml, ini) | 3 `test_json` + 2 `test_yaml` + 2 `test_xml` + 4 `test_csv` + 4 `test_tsv` + 2 `test_toml` + 2 `test_ini` + 7 CLI + 14 API | PASS |

**Total: 156 tests (146 passed, 10 skipped without LibreOffice)**

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
python -m pytest tests/test_xls.py -v     # Phase 9 (XLS)
python -m pytest tests/test_doc.py -v     # Phase 9 (DOC, requires LibreOffice)
python -m pytest tests/test_ppt.py -v     # Phase 9 (PPT, requires LibreOffice)
python -m pytest tests/test_txt.py -v     # Phase 9 (TXT)
python -m pytest tests/test_eml.py -v     # Phase 9 (EML)
python -m pytest tests/test_mht.py -v     # Phase 9 (MHT)
python -m pytest tests/test_md_parser.py -v  # Phase 9 (MD)
python -m pytest tests/test_rag.py -v     # Phase 10 (RAG)
python -m pytest tests/test_json.py -v   # Phase 11 (JSON)
python -m pytest tests/test_yaml.py -v   # Phase 11 (YAML)
python -m pytest tests/test_xml.py -v    # Phase 11 (XML)
python -m pytest tests/test_csv.py -v    # Phase 11 (CSV)
python -m pytest tests/test_tsv.py -v    # Phase 11 (TSV)
python -m pytest tests/test_toml.py -v   # Phase 11 (TOML)
python -m pytest tests/test_ini.py -v    # Phase 11 (INI)
```
