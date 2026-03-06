"""Parse TOML files to Markdown (code block)."""

from pathlib import Path


def parse(path: str) -> str:
    text = Path(path).read_text(encoding="utf-8")
    return f"```toml\n{text}\n```"
