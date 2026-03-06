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

Supported formats: `.docx`, `.pptx`, `.xlsx`, `.pdf`, `.xls`, `.doc`, `.ppt`, `.txt`, `.eml`, `.mht`/`.mhtml`, `.md`, `.json`, `.yaml`/`.yml`, `.xml`, `.csv`, `.tsv`, `.toml`, `.ini`/`.cfg`

> `.doc` and `.ppt` require LibreOffice to be installed.
> PDF math equations may render incorrectly — this is a known limitation of text-based PDF extraction.

## 3. Save output to a file

```bash
simple-parser report.pdf -o report.md
```

## 3a. RAG-optimized clean text

```bash
simple-parser document.docx --clean
```

The `--clean` flag strips markdown formatting, linearizes tables to key-value rows, and removes slide numbering — optimized for embedding models and RAG pipelines.

## 4. Use as a library

```python
from simple_parser.parser_docx import parse

markdown = parse("document.docx")
print(markdown)
```

Each parser module (`parser_docx`, `parser_pptx`, `parser_xlsx`, `parser_pdf`, `parser_xls`, `parser_doc`, `parser_ppt`, `parser_txt`, `parser_eml`, `parser_mht`, `parser_md`, `parser_json`, `parser_yaml`, `parser_xml`, `parser_csv`, `parser_tsv`, `parser_toml`, `parser_ini`) exposes the same `parse(path) -> str` function.

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

Open WebUI will automatically use simple-parser for all supported format parsing in Knowledge Base uploads. The `PUT /process` endpoint returns RAG-optimized clean text (no markdown formatting) for better embedding quality.

## 8. Run tests

```bash
pip install -e ".[api,dev]"
python -m pytest tests/ -v
```
