# Simple Parser - Implemented Features

## CLI (`cli.py`)
- **Format dispatch**: Routes `.docx`, `.pptx`, `.xlsx`, `.pdf`, `.xls`, `.doc`, `.ppt`, `.txt`, `.eml`, `.mht`, `.mhtml`, `.md` to their respective parsers
- **Stdout output**: Prints markdown to stdout by default
- **File output**: `-o` / `--output` flag writes to a file instead
- **Error handling**: File not found, unsupported format, corrupt ZIP, generic parse failures — all print to stderr and exit with code 1

## Markdown Utilities (`md.py`)
- `heading(text, level)` — ATX-style headings (`# ` through `###### `)
- `bold(text)` — `**text**`
- `italic(text)` — `*text*`
- `table(headers, rows)` — GFM pipe table with separator row, auto-pads short rows
- `escape(text)` — backslash-escapes markdown special characters
- `unordered_list(items)` — `- item` per line
- `ordered_list(items)` — `1. item` per line with auto-numbering

## DOCX Parser (`parser_docx.py`)
- Parses `word/document.xml` from ZIP archive
- **Headings**: Detects `Heading1`–`Heading6` paragraph styles → `#`–`######`
- **Paragraphs**: Plain text extraction from `w:r/w:t` runs
- **Bold/Italic**: Detects `w:b` and `w:i` in run properties → `**text**` / `*text*`
- **Tables**: `w:tbl` → GFM markdown table (first row as headers)
- **Lists**: Reads `word/numbering.xml` to distinguish bullet (`- item`) from numbered (`1. item`) lists, supports nesting via `w:ilvl`

## PPTX Parser (`parser_pptx.py`)
- Parses `ppt/slides/slide{N}.xml` from ZIP archive
- **Slide ordering**: Uses `ppt/_rels/presentation.xml.rels` for correct order, falls back to filename sorting
- **Titles**: Detects `p:ph type="title"` and `type="ctrTitle"` placeholders → `## Slide N: Title`
- **Body text**: Extracts all `a:t` text from non-title shapes

## XLSX Parser (`parser_xlsx.py`)
- Parses three XML files from ZIP: `xl/sharedStrings.xml`, `xl/workbook.xml`, `xl/worksheets/sheet{N}.xml`
- **Shared strings**: Resolves `t="s"` cell references to string table
- **Sheet names**: Each sheet outputs as `## Sheet: Name` + markdown table
- **Cell parsing**: Converts column letters (A, B, ..., AA, AB) to indices, handles both string and numeric values
- **Sparse rows**: Correctly handles gaps in cell references

## PDF Parser (`parser_pdf.py`)
- Uses PyMuPDF (`fitz`) — no OCR
- **Text extraction**: `page.get_text("dict")` for structured block/line/span data
- **Heading detection**: Font-size heuristic — computes modal body font size, then classifies larger text as `#` (≥1.8x), `##` (≥1.4x), or `###` (>1.1x)
- **Page separation**: Pages joined with `---` horizontal rules

## API Server (`api.py`)
- **FastAPI app** with optional `[api]` dependency group (keeps CLI lightweight)
- `GET /health` → `{"status": "ok"}`
- `POST /parse` → file upload, auto-detects format by extension
  - Response: `{"filename", "format", "markdown", "output_file", "parsed_at"}`
  - Writes upload to temp file, calls the appropriate parser, cleans up in `finally`
  - Saves parsed markdown to output directory (`OUTPUT_DIR` env var, defaults to `./output`)
  - Reuses same `PARSERS` dispatch dict as CLI
- **Error handling**: unsupported format → 400, corrupt file (`BadZipFile`) → 400, parse failure → 500, missing file → 422 (FastAPI auto)

## Open WebUI Integration (`PUT /process`)
- **External document loader** compatible with Open WebUI's `CONTENT_EXTRACTION_ENGINE=external`
- `PUT /process` accepts raw file bytes in request body (not multipart upload)
- **Format detection**: `X-Filename` header (URL-encoded) → extension, or `Content-Type` MIME → `MIME_TO_EXT` fallback
- **API key auth**: Optional — only enforced when `API_KEY` env var is set; checks `Authorization: Bearer <key>` header
- **Response format**: `{"page_content": str, "metadata": {"source": str, "format": str}}` — directly consumed by Open WebUI
- No file output saved — Open WebUI stores parsed content in its own vector DB

## XLS Parser (`parser_xls.py`)
- Uses `xlrd` library for BIFF format parsing
- Iterates sheets → rows → cells, integer detection (`v == int(v)` removes `.0`)
- Output matches XLSX format: `## Sheet: Name` + markdown table via `md.table()`

## DOC Parser (`parser_doc.py`)
- Converts `.doc` → `.docx` via `libreoffice --headless --convert-to docx`
- Reuses existing `parser_docx.parse()` on the converted file
- Clear `RuntimeError` with install instructions if LibreOffice not found
- Temporary directory for conversion, auto-cleaned

## PPT Parser (`parser_ppt.py`)
- Converts `.ppt` → `.pptx` via `libreoffice --headless --convert-to pptx`
- Reuses existing `parser_pptx.parse()` on the converted file
- Same error handling pattern as DOC parser

## TXT Parser (`parser_txt.py`)
- BOM-aware encoding detection chain: UTF-16LE BOM → UTF-16BE BOM → UTF-8 BOM → try UTF-8 → latin-1 fallback
- Strips BOM bytes before decoding
- No external dependencies (stdlib only)

## EML Parser (`parser_eml.py`)
- Uses stdlib `email.message_from_binary_file()` with `email.policy.default`
- Extracts Subject (as `# heading`), From, Date headers
- Walks MIME parts for `text/plain` body (fallback: `text/html` with tag stripping)
- Lists attachment filenames under `## Attachments`

## MHT/MHTML Parser (`parser_mht.py`)
- Parses MIME multipart structure using stdlib `email` module
- Finds `text/html` part and strips HTML tags via `HTMLParser` subclass
- Fallback to `text/plain` if no HTML part found
- Registered for both `.mht` and `.mhtml` extensions

## MD Parser (`parser_md.py`)
- Simple pass-through: `Path(path).read_text(encoding="utf-8")`
- Returns markdown content unchanged

## Docker
- **Dockerfile**: `python:3.10-slim`, installs `libreoffice-writer` + `libreoffice-impress` for DOC/PPT support, installs `.[api]`, runs uvicorn on port 8000
- **docker-compose.yml**: `api` service (port 8000, source + output volume mounts, `API_KEY` env var, `--reload`) + `open-webui` service (port 3000, `CONTENT_EXTRACTION_ENGINE=external`, auto-connects to `api` via Docker network)
- **.dockerignore**: Excludes `.git`, `tests/`, `__pycache__`, `.claude/`, `output/`, caches from build context
