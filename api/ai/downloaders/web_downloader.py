import time
from typing import Any

import markdown
from html2text import html2text
from html_to_draftjs import html_to_draftjs
from playwright._impl._errors import TimeoutError
from playwright.sync_api import sync_playwright


class WebDownloader:
    def download(self, url: str) -> dict[str, Any]:
        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch()
                page = browser.new_page()
                page.goto(url)
                # We wait for 2 seconds for the page to load
                time.sleep(2)
                result = page.content()
            except TimeoutError:
                result = page.content()
        markdown_string = html2text(result)

        html_string = markdown.markdown(markdown_string)
        content_state = html_to_draftjs(html_string)

        return content_state


__all__ = ["WebDownloader"]
