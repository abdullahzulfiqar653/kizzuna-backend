import time
from typing import Any

from django.utils import translation
from html2text import HTML2Text
from playwright._impl._errors import TimeoutError
from playwright.sync_api import sync_playwright

from api.ai.translator import google_translator
from api.utils.markdown import MarkdownProcessor


def remove_lines_before_header(markdown_string):
    """
    Detect the header 1 line and remove all the previous lines.
    Return the original markdown_string if no header 1 line is found.
    """
    lines = markdown_string.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("# "):
            return "\n".join(lines[i:])
    return markdown_string


def truncate(text):
    lines = []
    length = 0
    for line in text.split("\n"):
        # The content state json structure for each line is about 120 chars
        length += len(line) + 120
        if length > 220_000:
            lines.append("...[text is truncated because it is too long]")
            break
        lines.append(line)
    return "\n".join(lines)


class WebDownloader:
    translator = google_translator

    def download(self, url: str) -> dict[str, Any]:
        language = translation.get_language().split("-")[0]
        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch()
                page = browser.new_page()
                page.goto(url, timeout=10000)
                # We wait for 2 seconds for the page to load
                time.sleep(2)
                result = page.content()
            except TimeoutError:
                result = page.content()
        html2text = HTML2Text(baseurl=url)
        html2text.body_width = 0
        raw_markdown_string = html2text.handle(result)
        return (
            MarkdownProcessor(raw_markdown_string)
            .truncate()
            .remove_before_header()
            .fix_links()
            .set_translator(self.translator)
            .translate(language)
        )


__all__ = ["WebDownloader"]
