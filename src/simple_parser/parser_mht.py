"""Parse .mht/.mhtml (MIME HTML archive) files to Markdown."""

import email
import email.policy

from simple_parser import md


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

    return md.html_to_md(html)
