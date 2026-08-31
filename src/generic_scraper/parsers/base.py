"""The parser interface and the parsed-document value object.

A *parser* turns raw HTML into a :class:`Document`. Each processing type
(BeautifulSoup, lxml, ``html.parser``, regex) is an adapter behind this
interface. High-level policy depends only on :class:`Parser`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

BEAUTIFULSOUP = "beautifulsoup"
LXML = "lxml"
HTML_PARSER = "html.parser"
REGEX = "regex"

KNOWN_PROCESSING_TYPES = (BEAUTIFULSOUP, LXML, HTML_PARSER, REGEX)


@dataclass(frozen=True)
class Document:
    """A parsed page. Kept deliberately small and parser-agnostic."""

    title: str | None
    text: str
    html: str
    parser: str


@runtime_checkable
class Parser(Protocol):
    """Parses raw HTML into a :class:`Document`."""

    name: str

    def parse(self, html: str) -> Document:
        ...
