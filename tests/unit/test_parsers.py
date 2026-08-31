"""Unit tests for the four processing types."""

from __future__ import annotations

import pytest

from generic_scraper.errors import UnsupportedProcessingTypeError
from generic_scraper.parsers.base import KNOWN_PROCESSING_TYPES
from generic_scraper.parsers.registry import create_parser

PAGE = """
<!DOCTYPE html>
<html><head><title>Test Page</title></head>
<body><h1>Test Page</h1><p>alpha beta gamma</p>
<script>var ignored = 1;</script></body></html>
"""


@pytest.mark.parametrize("name", KNOWN_PROCESSING_TYPES)
def test_every_parser_extracts_the_title(name: str) -> None:
    parser = create_parser(name)

    document = parser.parse(PAGE)

    assert document.parser == name
    assert document.title == "Test Page"


@pytest.mark.parametrize("name", KNOWN_PROCESSING_TYPES)
def test_every_parser_extracts_visible_text_and_drops_scripts(name: str) -> None:
    document = create_parser(name).parse(PAGE)

    assert "alpha beta gamma" in document.text
    assert "ignored" not in document.text


@pytest.mark.parametrize("name", KNOWN_PROCESSING_TYPES)
def test_every_parser_handles_a_page_with_no_title(name: str) -> None:
    document = create_parser(name).parse("<html><body>hi</body></html>")

    assert document.title is None


@pytest.mark.parametrize("name", KNOWN_PROCESSING_TYPES)
def test_every_parser_handles_empty_html(name: str) -> None:
    document = create_parser(name).parse("")

    assert document.title is None
    assert document.text == ""


def test_unknown_processing_type_is_rejected() -> None:
    with pytest.raises(UnsupportedProcessingTypeError, match="xml"):
        create_parser("xml")
