"""Parse .eml (RFC 2822) email files to Markdown."""

import email
import email.policy
from html.parser import HTMLParser

from simple_parser import md


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

    blocks: list[str] = []

    subject = msg.get("Subject", "")
    if subject:
        blocks.append(md.heading(subject, 1))

    from_addr = msg.get("From", "")
    if from_addr:
        blocks.append(f"{md.bold('From:')} {from_addr}")

    date = msg.get("Date", "")
    if date:
        blocks.append(f"{md.bold('Date:')} {date}")

    # Extract body
    body = ""
    for part in msg.walk():
        ct = part.get_content_type()
        if ct == "text/plain":
            body = part.get_content()
            break
        if ct == "text/html" and not body:
            body = _strip_html(part.get_content())

    if body:
        blocks.append(body.strip())

    # List attachments
    attachments = []
    for part in msg.walk():
        fn = part.get_filename()
        if fn:
            attachments.append(fn)
    if attachments:
        blocks.append(md.heading("Attachments", 2))
        blocks.append(md.unordered_list(attachments))

    return "\n\n".join(blocks)
