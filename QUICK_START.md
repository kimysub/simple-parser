# Quick Start

## 1. Install

```bash
cd simple-parser
pip install -e .
```

## 2. Parse a document

```bash
simple-parser path/to/file.docx
```

Supported formats: `.docx`, `.pptx`, `.xlsx`, `.pdf`

## 3. Save output to a file

```bash
simple-parser report.pdf -o report.md
```

## 4. Use as a library

```python
from simple_parser.parser_docx import parse

markdown = parse("document.docx")
print(markdown)
```

Each parser module (`parser_docx`, `parser_pptx`, `parser_xlsx`, `parser_pdf`) exposes the same `parse(path) -> str` function.

## 5. Run the API server

```bash
pip install -e ".[api]"
uvicorn simple_parser.api:app --reload
```

```bash
# Health check
curl localhost:8000/health

# Parse a file
curl -X POST localhost:8000/parse -F "file=@document.docx"
```

## 6. Run with Docker

```bash
docker compose up
# API available at http://localhost:8000
# Parsed markdown files saved to ./output/
```

## 7. Open WebUI Integration

```bash
# Set a shared API key
export API_KEY=my-secret-key

# Start simple-parser + Open WebUI together
docker compose up

# Open WebUI: http://localhost:3000
# simple-parser API: http://localhost:8000
```

Open WebUI will automatically use simple-parser for docx/pptx/xlsx/pdf parsing in Knowledge Base uploads.

## 8. Run tests

```bash
pip install -e ".[api,dev]"
python -m pytest tests/ -v
```
