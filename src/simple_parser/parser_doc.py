"""Parse .doc (legacy Word) files to Markdown via LibreOffice conversion."""

import shutil
import subprocess
import tempfile
from pathlib import Path

from simple_parser import parser_docx


def parse(path: str) -> str:
    if not shutil.which("libreoffice"):
        raise RuntimeError(
            "LibreOffice is required to parse .doc files. "
            "Install it: apt-get install libreoffice-writer (Linux) "
            "or brew install --cask libreoffice (macOS)"
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            ["libreoffice", "--headless", "--convert-to", "docx", "--outdir", tmpdir, path],
            capture_output=True,
            timeout=60,
        )
        if result.returncode != 0:
            raise RuntimeError(f"LibreOffice conversion failed: {result.stderr.decode()}")

        converted = Path(tmpdir) / (Path(path).stem + ".docx")
        if not converted.exists():
            raise RuntimeError("LibreOffice conversion produced no output file")

        return parser_docx.parse(str(converted))
