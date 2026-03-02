"""Shared markdown output helpers."""

import re

_ESCAPE_RE = re.compile(r"([\\`*_\{\}\[\]()#+\-.!|~>])")


def heading(text: str, level: int) -> str:
    return f"{'#' * level} {text}"


def bold(text: str) -> str:
    return f"**{text}**"


def italic(text: str) -> str:
    return f"*{text}*"


def table(headers: list[str], rows: list[list[str]]) -> str:
    header_line = "| " + " | ".join(headers) + " |"
    sep_line = "| " + " | ".join("---" for _ in headers) + " |"
    lines = [header_line, sep_line]
    for row in rows:
        # Pad row to match header count
        padded = row + [""] * (len(headers) - len(row))
        lines.append("| " + " | ".join(padded[:len(headers)]) + " |")
    return "\n".join(lines)


def escape(text: str) -> str:
    return _ESCAPE_RE.sub(r"\\\1", text)


def unordered_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def ordered_list(items: list[str]) -> str:
    return "\n".join(f"{i}. {item}" for i, item in enumerate(items, 1))
