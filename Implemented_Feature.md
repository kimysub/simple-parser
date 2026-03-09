# Simple Parser - Implemented Features

## CLI (`cli.py`)
- **Format dispatch**: Routes `.docx`, `.pptx`, `.xlsx`, `.pdf`, `.xls`, `.doc`, `.ppt`, `.txt`, `.eml`, `.mht`, `.mhtml`, `.md`, `.json`, `.yaml`, `.yml`, `.xml`, `.csv`, `.tsv`, `.toml`, `.ini`, `.cfg` to their respective parsers
- **Stdout output**: Prints markdown to stdout by default
- **File output**: `-o` / `--output` flag writes to a file instead
- **Clean text output**: `--clean` flag strips markdown formatting for RAG-optimized output
- **Error handling**: File not found, unsupported format, corrupt ZIP, generic parse failures — all print to stderr and exit with code 1

## Markdown Utilities (`md.py`)
- `heading(text, level)` — ATX-style headings (`# ` through `###### `)
- `bold(text)` — `**text**`
- `italic(text)` — `*text*`
- `table(headers, rows)` — GFM pipe table with separator row, auto-pads short rows
- `escape(text)` — backslash-escapes markdown special characters
- `unordered_list(items)` — `- item` per line
- `ordered_list(items)` — `1. item` per line with auto-numbering
- `html_to_md(html)` — converts HTML to Markdown (headings, bold, italic, links, lists, images, code, blockquotes, tables)

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
- **Tables**: Detects `a:tbl` (DrawingML tables) inside `p:graphicFrame` elements, extracts header row + data rows from `a:tr`/`a:tc` → markdown tables
- **Whitespace collapse**: Multiple consecutive spaces collapsed to single space (common in PPTX with split text runs across `a:t` elements)

## XLSX Parser (`parser_xlsx.py`)
- Parses three XML files from ZIP: `xl/sharedStrings.xml`, `xl/workbook.xml`, `xl/worksheets/sheet{N}.xml`
- **Shared strings**: Resolves `t="s"` cell references to string table
- **Sheet names**: Each sheet outputs as `## Sheet: Name` + markdown table
- **Cell parsing**: Converts column letters (A, B, ..., AA, AB) to indices, handles both string and numeric values
- **Sparse rows**: Correctly handles gaps in cell references

## PDF Parser (`parser_pdf.py`)
- Uses PyMuPDF (`fitz`) — no OCR
- **Text extraction**: `page.get_text("dict")` for structured block/line/span data
- **Bordered table detection**: `page.find_tables()` detects tables by cell boundaries, extracts as markdown tables, and excludes table regions from regular text extraction via rectangle overlap check to prevent duplication
- **Borderless table detection**: Detects academic-style tables without borders — matches `Table N:` pattern, then groups subsequent blocks as header + data using per-line column grouping or multi-space splitting; preserves table captions in output
- **Smart body size detection**: Rounds font sizes to nearest integer to merge rendering variations, then uses the largest size with significant share (>5% of total chars AND >200 chars) as effective body size — avoids treating common sub-heading sizes as headings
- **Heading detection**: Font-size heuristic with strict `<` boundary — classifies text as `#` (≥1.8x body), `##` (≥1.4x), or `###` (≥1.2x); heading min length (10 chars) filters short labels, heading max length (200 chars) filters paragraphs
- **Ligature normalization**: Converts typographic ligatures to plain text (ﬁ→fi, ﬂ→fl, ﬀ→ff, ﬃ→ffi, ﬄ→ffl)
- **Whitespace collapse**: Multiple consecutive spaces collapsed to single space (common in PDFs with positioned text)
- **Page separation**: Pages joined with `---` horizontal rules
- **Known limitation**: Mathematical equations may render incorrectly. PDFs store equations as individually positioned glyphs (not LaTeX/MathML), so spatial constructs like summations, fractions, superscripts, and subscripts get fragmented during text extraction. This is a fundamental limitation of text-based PDF extraction without OCR/vision models.

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
- **RAG post-processing**: `page_content` is automatically cleaned via `rag.clean_for_rag()` — strips markdown formatting, linearizes tables, removes slide numbering for optimal embedding quality
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
- Walks MIME parts for `text/plain` body (fallback: `text/html` with HTML-to-Markdown conversion via `md.html_to_md()`)
- Lists attachment filenames under `## Attachments`

## MHT/MHTML Parser (`parser_mht.py`)
- Parses MIME multipart structure using stdlib `email` module
- Finds `text/html` part and converts to Markdown via `md.html_to_md()` (headings, bold, links, lists preserved)
- Fallback to `text/plain` if no HTML part found
- Registered for both `.mht` and `.mhtml` extensions

## MD Parser (`parser_md.py`)
- Simple pass-through: `Path(path).read_text(encoding="utf-8")`
- Returns markdown content unchanged

## JSON Parser (`parser_json.py`)
- Pretty-prints JSON with `json.dumps(indent=2, ensure_ascii=False)`
- Wraps output in ````json` fenced code block
- No external dependencies (stdlib `json`)

## YAML Parser (`parser_yaml.py`)
- Reads text content and wraps in ````yaml` fenced code block
- Registered for both `.yaml` and `.yml` extensions
- No external dependencies

## XML Parser (`parser_xml.py`)
- Reads text content and wraps in ````xml` fenced code block
- No external dependencies

## CSV Parser (`parser_csv.py`)
- Parses with stdlib `csv.reader`, first row as headers, remaining as data
- Outputs markdown table via `md.table()`
- Skips empty rows

## TSV Parser (`parser_tsv.py`)
- Parses with stdlib `csv.reader(delimiter='\t')`, same structure as CSV
- Outputs markdown table via `md.table()`

## TOML Parser (`parser_toml.py`)
- Reads text content and wraps in ````toml` fenced code block
- No external dependencies

## INI Parser (`parser_ini.py`)
- Reads text content and wraps in ````ini` fenced code block
- Registered for both `.ini` and `.cfg` extensions
- No external dependencies

## RAG Post-Processor (`rag.py`)
- `clean_for_rag(markdown)` converts markdown to clean text optimized for embedding models
- **Table linearization**: `| Name | Age |\n| --- | --- |\n| Alice | 30 |` → `Name: Alice; Age: 30`
- **Heading stripping**: `# Title` → `Title`
- **Bold/italic removal**: `**text**` / `*text*` → `text`
- **Link conversion**: `[text](url)` → `text (url)`
- **Image conversion**: `![alt](src)` → `alt`
- **Slide prefix removal**: `Slide 1: Title` → `Title`
- **Code block cleaning**: Removes ``` markers, keeps content
- **Horizontal rule removal**: `---` → removed
- **Whitespace normalization**: Collapses 3+ newlines to 2
- Automatically applied in `PUT /process` endpoint for Open WebUI RAG
- Available via `--clean` CLI flag

## Docker
- **Dockerfile**: `python:3.10-slim`, installs `libreoffice-writer` + `libreoffice-impress` for DOC/PPT support, installs `.[api]`, runs uvicorn on port 8000
- **docker-compose.yml**: `api` service (port 8000, source + output volume mounts, `API_KEY` env var, `--reload`) + `open-webui` service (port 3000, `CONTENT_EXTRACTION_ENGINE=external`, auto-connects to `api` via Docker network)
- **.dockerignore**: Excludes `.git`, `tests/`, `__pycache__`, `.claude/`, `output/`, caches from build context
