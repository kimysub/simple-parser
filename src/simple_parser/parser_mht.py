"""Parse .mht/.mhtml (MIME HTML archive) files to Markdown."""

import email
import email.policy
from html.parser import HTMLParser


class _TagStripper(HTMLParser):
    """Minimal HTML tag stripper."""

    def __init__(self):
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return "".join(self._parts)


def _strip_html(html: str) -> str:
    s = _TagStripper()
    s.feed(html)
    return s.get_text()


def parse(path: str) -> str:
    with open(path, "rb") as f:
        msg = email.message_from_binary_file(f, policy=email.policy.default)

    # Find text/html part
    html = ""
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            html = part.get_content()
            break

    if not html:
        # Fallback: try text/plain
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_content().strip()

    return _strip_html(html).strip()
