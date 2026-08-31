"""Registry mapping a processing-type name to a parser.

Adding a parser means registering a factory here; nothing else in the package
needs to change.
"""

from __future__ import annotations

from collections.abc import Callable

from generic_scraper.errors import UnsupportedProcessingTypeError
from generic_scraper.parsers.base import (
    BEAUTIFULSOUP,
    HTML_PARSER,
    LXML,
    REGEX,
    Parser,
)
from generic_scraper.parsers.implementations import (
    BeautifulSoupParser,
    HtmlDotParser,
    LxmlParser,
    RegexParser,
)

_PARSERS: dict[str, Callable[[], Parser]] = {
    BEAUTIFULSOUP: BeautifulSoupParser,
    LXML: LxmlParser,
    HTML_PARSER: HtmlDotParser,
    REGEX: RegexParser,
}


def create_parser(name: str) -> Parser:
    """Return a fresh parser for ``name``. Raises for an unknown name."""

    try:
        factory = _PARSERS[name]
    except KeyError:
        raise UnsupportedProcessingTypeError(
            f"UnsupportedProcessingTypeError: {name!r} is not a supported "
            f"processing type; choose one of {', '.join(_PARSERS)}"
        ) from None
    return factory()
