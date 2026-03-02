"""CLI entry point: parse document files to Markdown."""

import argparse
import sys
import zipfile
from pathlib import Path

from simple_parser import parser_docx, parser_pptx, parser_xlsx, parser_pdf

PARSERS = {
    ".docx": parser_docx.parse,
    ".pptx": parser_pptx.parse,
    ".xlsx": parser_xlsx.parse,
    ".pdf": parser_pdf.parse,
}

SUPPORTED = ", ".join(PARSERS)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="simple-parser",
        description="Parse document files (docx, pptx, xlsx, pdf) into Markdown.",
    )
    parser.add_argument("file", help="Path to the document file")
    parser.add_argument(
        "-o", "--output", help="Output file path (default: stdout)", default=None
    )
    args = parser.parse_args(argv)

    path = Path(args.file)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    ext = path.suffix.lower()
    parse_fn = PARSERS.get(ext)
    if parse_fn is None:
        print(
            f"Error: unsupported format '{ext}'. Supported: {SUPPORTED}",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        result = parse_fn(str(path))
    except zipfile.BadZipFile:
        print(f"Error: corrupt or invalid file: {path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: failed to parse {path}: {e}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
    else:
        print(result)


if __name__ == "__main__":
    main()
