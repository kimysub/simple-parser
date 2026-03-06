"""CLI entry point: parse document files to Markdown."""

import argparse
import sys
import zipfile
from pathlib import Path

from simple_parser import (
    parser_csv,
    parser_doc,
    parser_docx,
    parser_eml,
    parser_ini,
    parser_json,
    parser_md,
    parser_mht,
    parser_pdf,
    parser_ppt,
    parser_pptx,
    parser_toml,
    parser_tsv,
    parser_txt,
    parser_xls,
    parser_xlsx,
    parser_xml,
    parser_yaml,
    rag,
)

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
    ".json": parser_json.parse,
    ".yaml": parser_yaml.parse,
    ".yml": parser_yaml.parse,
    ".xml": parser_xml.parse,
    ".csv": parser_csv.parse,
    ".tsv": parser_tsv.parse,
    ".toml": parser_toml.parse,
    ".ini": parser_ini.parse,
    ".cfg": parser_ini.parse,
}

SUPPORTED = ", ".join(PARSERS)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="simple-parser",
        description="Parse document files (docx, pptx, xlsx, pdf, xls, doc, ppt, txt, eml, mht, md, json, yaml, xml, csv, tsv, toml, ini) into Markdown.",
    )
    parser.add_argument("file", help="Path to the document file")
    parser.add_argument(
        "-o", "--output", help="Output file path (default: stdout)", default=None
    )
    parser.add_argument(
        "--clean", action="store_true",
        help="Strip markdown formatting for RAG-optimized clean text output",
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

    if args.clean:
        result = rag.clean_for_rag(result)

    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
    else:
        print(result)


if __name__ == "__main__":
    main()
