"""Concrete parsers, one per processing type.

Each parser extracts a title and visible text. They differ only in the library
they lean on, which is the point: a caller picks a processing type and gets a
uniform :class:`Document` back.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser as _StdHTMLParser

from generic_scraper.parsers.base import (
    BEAUTIFULSOUP,
    HTML_PARSER,
    LXML,
    REGEX,
    Document,
)

_WHITESPACE = re.compile(r"\s+")
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_SCRIPT_STYLE_RE = re.compile(
    r"<(script|style)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL
)


def _clean(text: str) -> str:
    return _WHITESPACE.sub(" ", text).strip()


class BeautifulSoupParser:
    name = BEAUTIFULSOUP

    def parse(self, html: str) -> Document:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.string if soup.title else None
        return Document(
            title=_clean(title) if title else None,
            text=_clean(soup.get_text(" ")),
            html=html,
            parser=self.name,
        )


class LxmlParser:
    name = LXML

    def parse(self, html: str) -> Document:
        import lxml.html

        root = lxml.html.fromstring(html) if html.strip() else None
        if root is None:
            return Document(title=None, text="", html=html, parser=self.name)
        title = root.findtext(".//title")
        for element in root.iter("script", "style"):
            element.text = None
        return Document(
            title=_clean(title) if title else None,
            text=_clean(root.text_content()),
            html=html,
            parser=self.name,
        )


class _TitleTextExtractor(_StdHTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_title = False
        self._skip_depth = 0
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: object) -> None:
        if tag == "title":
            self._in_title = True
        elif tag in ("script", "style"):
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        elif tag in ("script", "style") and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)
        elif self._skip_depth == 0:
            self.text_parts.append(data)


class HtmlDotParser:
    name = HTML_PARSER

    def parse(self, html: str) -> Document:
        extractor = _TitleTextExtractor()
        extractor.feed(html)
        title = _clean("".join(extractor.title_parts))
        return Document(
            title=title or None,
            text=_clean(" ".join(extractor.text_parts)),
            html=html,
            parser=self.name,
        )


class RegexParser:
    name = REGEX

    def parse(self, html: str) -> Document:
        match = _TITLE_RE.search(html)
        title = _clean(match.group(1)) if match else None
        stripped = _SCRIPT_STYLE_RE.sub(" ", html)
        text = _clean(_TAG_RE.sub(" ", stripped))
        return Document(
            title=title or None,
            text=text,
            html=html,
            parser=self.name,
        )
