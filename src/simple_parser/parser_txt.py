"""Parse plain text files to Markdown with BOM-aware encoding detection."""

from pathlib import Path


def parse(path: str) -> str:
    raw = Path(path).read_bytes()

    # BOM detection
    if raw[:2] == b"\xff\xfe":
        return raw[2:].decode("utf-16-le")
    if raw[:2] == b"\xfe\xff":
        return raw[2:].decode("utf-16-be")
    if raw[:3] == b"\xef\xbb\xbf":
        return raw[3:].decode("utf-8")

    # Try UTF-8, fall back to latin-1
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1")
