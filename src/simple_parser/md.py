"""Shared markdown output helpers."""

import re
from html.parser import HTMLParser

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


# --- HTML to Markdown ---

_BLOCK_TAGS = {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "pre", "tr", "hr"}
_HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
_INLINE_BOLD = {"b", "strong"}
_INLINE_ITALIC = {"i", "em"}


class _HtmlToMd(HTMLParser):
    """Convert HTML to Markdown."""

    def __init__(self):
        super().__init__()
        self._out: list[str] = []
        self._tag_stack: list[str] = []
        self._list_stack: list[str] = []  # "ul" or "ol"
        self._ol_counters: list[int] = []
        self._href: str | None = None
        self._link_text: list[str] = []
        self._in_link = False
        self._in_pre = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        self._tag_stack.append(tag)
        attr_dict = dict(attrs)

        if tag in _HEADING_TAGS:
            self._out.append("\n\n")
        elif tag == "p" or tag == "div":
            self._out.append("\n\n")
        elif tag == "br":
            self._out.append("\n")
        elif tag == "hr":
            self._out.append("\n\n---\n\n")
        elif tag in _INLINE_BOLD:
            self._out.append("**")
        elif tag in _INLINE_ITALIC:
            self._out.append("*")
        elif tag == "code" and not self._in_pre:
            self._out.append("`")
        elif tag == "pre":
            self._in_pre = True
            self._out.append("\n\n```\n")
        elif tag == "blockquote":
            self._out.append("\n\n> ")
        elif tag == "a":
            self._href = attr_dict.get("href")
            self._in_link = True
            self._link_text = []
        elif tag == "img":
            alt = attr_dict.get("alt", "")
            src = attr_dict.get("src", "")
            self._out.append(f"![{alt}]({src})")
        elif tag == "ul":
            self._list_stack.append("ul")
            self._out.append("\n")
        elif tag == "ol":
            self._list_stack.append("ol")
            self._ol_counters.append(0)
            self._out.append("\n")
        elif tag == "li":
            depth = max(0, len(self._list_stack) - 1)
            indent = "  " * depth
            if self._list_stack and self._list_stack[-1] == "ol":
                self._ol_counters[-1] += 1
                self._out.append(f"\n{indent}{self._ol_counters[-1]}. ")
            else:
                self._out.append(f"\n{indent}- ")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self._tag_stack and self._tag_stack[-1] == tag:
            self._tag_stack.pop()

        if tag in _HEADING_TAGS:
            level = int(tag[1])
            # Prepend heading marker to the text accumulated since starttag
            # Find last \n\n and insert heading prefix after it
            text = self._flush_trailing_text()
            self._out.append(f"{'#' * level} {text.strip()}\n\n")
        elif tag in _INLINE_BOLD:
            self._out.append("**")
        elif tag in _INLINE_ITALIC:
            self._out.append("*")
        elif tag == "code" and not self._in_pre:
            self._out.append("`")
        elif tag == "pre":
            self._in_pre = False
            self._out.append("\n```\n\n")
        elif tag == "blockquote":
            self._out.append("\n\n")
        elif tag == "a":
            text = "".join(self._link_text)
            if self._href:
                self._out.append(f"[{text}]({self._href})")
            else:
                self._out.append(text)
            self._in_link = False
            self._href = None
            self._link_text = []
        elif tag == "ul":
            if self._list_stack and self._list_stack[-1] == "ul":
                self._list_stack.pop()
            self._out.append("\n")
        elif tag == "ol":
            if self._list_stack and self._list_stack[-1] == "ol":
                self._list_stack.pop()
            if self._ol_counters:
                self._ol_counters.pop()
            self._out.append("\n")

    def handle_data(self, data: str) -> None:
        if self._in_link:
            self._link_text.append(data)
        else:
            self._out.append(data)

    def _flush_trailing_text(self) -> str:
        """Pop text back to last \\n\\n for heading construction."""
        parts = []
        while self._out and self._out[-1] != "\n\n":
            parts.append(self._out.pop())
        # Remove the \n\n separator too
        if self._out and self._out[-1] == "\n\n":
            self._out.pop()
        parts.reverse()
        return "".join(parts)

    def get_markdown(self) -> str:
        raw = "".join(self._out)
        # Collapse 3+ newlines to 2
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        return raw.strip()


def html_to_md(html: str) -> str:
    """Convert an HTML string to Markdown."""
    converter = _HtmlToMd()
    converter.feed(html)
    return converter.get_markdown()
