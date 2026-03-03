"""Parse Markdown files — pass-through."""

from pathlib import Path


def parse(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")
