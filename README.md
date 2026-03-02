# Simple Parser

CLI tool to parse document files (docx, pptx, xlsx, pdf) into Markdown.

## Features

- **DOCX**: Headings, paragraphs, bold/italic, tables, bullet/numbered lists
- **PPTX**: Slide titles, body text, correct slide ordering
- **XLSX**: Sheet names, shared strings, numeric values → markdown tables
- **PDF**: Text extraction via PyMuPDF, font-size based heading detection
- **API**: FastAPI web server with `POST /parse` and `PUT /process` endpoints for HTTP-based parsing
- **Open WebUI**: Compatible with Open WebUI's external document loader (`CONTENT_EXTRACTION_ENGINE=external`)
- No OCR — fast, lightweight, XML-based parsing for Office formats

## Requirements

- Python 3.10+
- PyMuPDF (`pymupdf`) for PDF support

## Installation

```bash
# CLI only
pip install -e .

# With API server
pip install -e ".[api]"

# With dev tools (pytest, httpx, ruff)
pip install -e ".[api,dev]"
```

## Usage

### CLI

```bash
# Parse to stdout
simple-parser document.docx
simple-parser presentation.pptx
simple-parser spreadsheet.xlsx
simple-parser report.pdf

# Save to file
simple-parser document.docx -o output.md
```

### API Server

```bash
# Start the server
uvicorn simple_parser.api:app --reload

# Health check
curl localhost:8000/health

# Parse a file
curl -X POST localhost:8000/parse -F "file=@document.docx"
```

### Docker

```bash
# With docker-compose (dev mode, hot-reload)
docker compose up
# Parsed files saved to ./output/ on the host

# Or build and run directly
docker build -t simple-parser .
docker run -p 8000:8000 simple-parser
```

### Open WebUI Integration

simple-parser can serve as Open WebUI's external document loader for Knowledge Base uploads.

```bash
# Set a shared API key
export API_KEY=my-secret-key

# Start both services
docker compose up

# Open WebUI available at http://localhost:3000
# simple-parser API at http://localhost:8000
```

Open WebUI sends `PUT /process` with raw file bytes, and simple-parser returns `{"page_content", "metadata"}`.

Manual test:
```bash
curl -X PUT http://localhost:8000/process \
  -H "X-Filename: sample.docx" \
  -H "Authorization: Bearer my-secret-key" \
  --data-binary @tests/fixtures/sample.docx
```

## Project Structure

```
src/simple_parser/
  cli.py             # CLI entry point (argparse, format dispatch)
  api.py             # FastAPI server (/health, /parse, /process endpoints)
  md.py              # Shared markdown output helpers
  parser_docx.py     # DOCX → Markdown
  parser_pptx.py     # PPTX → Markdown
  parser_xlsx.py     # XLSX → Markdown
  parser_pdf.py      # PDF  → Markdown
```

## How It Works

Office formats (docx, pptx, xlsx) are ZIP archives containing XML. The parsers use Python's stdlib `zipfile` + `xml.etree.ElementTree` to extract content — no external Office dependencies needed.

PDF parsing uses PyMuPDF (`fitz`) for non-OCR text extraction with a font-size heuristic for heading detection.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check → `{"status": "ok"}` |
| `POST` | `/parse` | Upload a file → `{"filename", "format", "markdown", "output_file", "parsed_at"}` |
| `PUT` | `/process` | Open WebUI compatible — raw bytes → `{"page_content", "metadata"}` |

**`POST /parse`**: Parsed markdown is automatically saved to the output directory (`./output` by default, configurable via `OUTPUT_DIR` env var). In Docker, `./output` is volume-mounted to the host.

**`PUT /process`**: Accepts raw file bytes in the request body. File format is determined from the `X-Filename` header (URL-encoded filename) or `Content-Type` MIME type as fallback. Supports optional `Authorization: Bearer <key>` when `API_KEY` env var is set.

Error responses: 400 (unsupported format / corrupt file / empty body), 401 (invalid API key), 422 (missing file), 500 (parse failure).

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Lint
ruff check src/ tests/
```

## Parser Interface

Each parser exposes a uniform interface:

```python
def parse(path: str) -> str
```

Takes a file path, returns a Markdown string.
