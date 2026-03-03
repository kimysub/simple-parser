"""FastAPI server for simple-parser."""

import os
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

from fastapi import FastAPI, HTTPException, Request, UploadFile

from simple_parser import (
    parser_doc,
    parser_docx,
    parser_eml,
    parser_md,
    parser_mht,
    parser_pdf,
    parser_ppt,
    parser_pptx,
    parser_txt,
    parser_xls,
    parser_xlsx,
)

app = FastAPI(title="simple-parser")

OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "./output"))

PARSERS = {
    ".docx": parser_docx.parse,
    ".pptx": parser_pptx.parse,
    ".xlsx": parser_xlsx.parse,
    ".pdf": parser_pdf.parse,
    ".xls": parser_xls.parse,
    ".doc": parser_doc.parse,
    ".ppt": parser_ppt.parse,
    ".txt": parser_txt.parse,
    ".eml": parser_eml.parse,
    ".mht": parser_mht.parse,
    ".mhtml": parser_mht.parse,
    ".md": parser_md.parse,
}

SUPPORTED = ", ".join(PARSERS)

MIME_TO_EXT = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.ms-excel": ".xls",
    "application/msword": ".doc",
    "application/vnd.ms-powerpoint": ".ppt",
    "text/plain": ".txt",
    "message/rfc822": ".eml",
    "multipart/related": ".mht",
    "text/markdown": ".md",
}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/parse")
async def parse(file: UploadFile):
    ext = Path(file.filename).suffix.lower()
    parse_fn = PARSERS.get(ext)
    if parse_fn is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{ext}'. Supported: {SUPPORTED}",
        )

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        markdown = parse_fn(tmp_path)
    except zipfile.BadZipFile:
        raise HTTPException(
            status_code=400, detail=f"Corrupt or invalid file: {file.filename}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to parse {file.filename}: {e}"
        )
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stem = Path(file.filename).stem
    output_path = OUTPUT_DIR / f"{stem}.md"
    output_path.write_text(markdown, encoding="utf-8")

    return {
        "filename": file.filename,
        "format": ext,
        "markdown": markdown,
        "output_file": str(output_path),
        "parsed_at": datetime.now(timezone.utc).isoformat(),
    }


@app.put("/process")
async def process(request: Request):
    """Open WebUI compatible endpoint: raw bytes in, page_content out."""
    api_key = os.environ.get("API_KEY")
    if api_key:
        auth = request.headers.get("authorization", "")
        if auth != f"Bearer {api_key}":
            raise HTTPException(status_code=401, detail="Invalid or missing API key")

    data = await request.body()
    if not data:
        raise HTTPException(status_code=400, detail="Empty request body")

    x_filename = request.headers.get("x-filename")
    filename = unquote(x_filename) if x_filename else None
    ext = Path(filename).suffix.lower() if filename else None

    if not ext or ext not in PARSERS:
        ct = request.headers.get("content-type", "")
        mime = ct.split(";")[0].strip().lower()
        ext = MIME_TO_EXT.get(mime)

    if not ext or ext not in PARSERS:
        raise HTTPException(status_code=400, detail=f"Unsupported format. Supported: {SUPPORTED}")
    parse_fn = PARSERS[ext]

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        markdown = parse_fn(tmp_path)
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Corrupt or invalid file")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse: {e}")
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)

    return {
        "page_content": markdown,
        "metadata": {
            "source": filename or "unknown",
            "format": ext,
        },
    }
