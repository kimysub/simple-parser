"""Parse JSON files to Markdown (pretty-printed code block)."""

import json
from pathlib import Path


def parse(path: str) -> str:
    raw = Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    pretty = json.dumps(data, indent=2, ensure_ascii=False)
    return f"```json\n{pretty}\n```"
