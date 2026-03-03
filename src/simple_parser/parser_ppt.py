"""Parse .ppt (legacy PowerPoint) files to Markdown via LibreOffice conversion."""

import shutil
import subprocess
import tempfile
from pathlib import Path

from simple_parser import parser_pptx


def parse(path: str) -> str:
    if not shutil.which("libreoffice"):
        raise RuntimeError(
            "LibreOffice is required to parse .ppt files. "
            "Install it: apt-get install libreoffice-impress (Linux) "
            "or brew install --cask libreoffice (macOS)"
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            ["libreoffice", "--headless", "--convert-to", "pptx", "--outdir", tmpdir, path],
            capture_output=True,
            timeout=60,
        )
        if result.returncode != 0:
            raise RuntimeError(f"LibreOffice conversion failed: {result.stderr.decode()}")

        converted = Path(tmpdir) / (Path(path).stem + ".pptx")
        if not converted.exists():
            raise RuntimeError("LibreOffice conversion produced no output file")

        return parser_pptx.parse(str(converted))
