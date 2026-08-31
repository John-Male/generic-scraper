"""Property tests: the four processing types agree on well-formed pages."""

from __future__ import annotations

import random

import pytest

from generic_scraper.parsers.base import KNOWN_PROCESSING_TYPES, Document
from generic_scraper.parsers.registry import create_parser
from tests.property.framework import for_all, words

pytestmark = pytest.mark.property


def _page(rng: random.Random) -> tuple[str, str, list[str]]:
    """Build a simple page; return (html, expected_title, body_words)."""

    title = words(rng, low=1, high=5)
    body_words = words(rng, low=1, high=10).split()
    paragraphs = "".join(f"<p>{w}</p>" for w in body_words)
    noise = "<script>var x = 1;</script><style>.a{color:red}</style>"
    html = (
        "<!DOCTYPE html><html><head>"
        f"<title>{title}</title></head><body>"
        f"<h1>heading</h1>{paragraphs}{noise}</body></html>"
    )
    return html, title, body_words


def _documents(html: str) -> list[Document]:
    return [create_parser(name).parse(html) for name in KNOWN_PROCESSING_TYPES]


def test_every_parser_recovers_the_title() -> None:
    def prop(page: tuple[str, str, list[str]]) -> None:
        html, expected_title, _words = page
        for name in KNOWN_PROCESSING_TYPES:
            document = create_parser(name).parse(html)
            assert document.title == expected_title
            assert document.parser == name

    for_all(_page, prop, cases=120)


def test_all_parsers_agree_on_the_title() -> None:
    def prop(page: tuple[str, str, list[str]]) -> None:
        html, _title, _words = page
        titles = {doc.title for doc in _documents(html)}
        assert len(titles) == 1

    for_all(_page, prop, cases=120)


def test_body_words_survive_and_script_text_does_not() -> None:
    def prop(page: tuple[str, str, list[str]]) -> None:
        html, _title, body_words = page
        for name in KNOWN_PROCESSING_TYPES:
            text = create_parser(name).parse(html).text
            for word in body_words:
                assert word in text
            assert "var x" not in text
            assert "color:red" not in text

    for_all(_page, prop, cases=120)


def test_parsing_preserves_the_raw_html_and_is_idempotent() -> None:
    def prop(page: tuple[str, str, list[str]]) -> None:
        html, _title, _words = page
        for name in KNOWN_PROCESSING_TYPES:
            parser = create_parser(name)
            first = parser.parse(html)
            second = create_parser(name).parse(html)
            assert first.html == html
            assert first == second

    for_all(_page, prop, cases=80)


def test_blank_pages_parse_to_an_empty_document() -> None:
    def prop(blank: str) -> None:
        for name in KNOWN_PROCESSING_TYPES:
            document = create_parser(name).parse(blank)
            assert document.title is None
            assert document.text == ""

    for_all(
        lambda rng: rng.choice(("", "   ", "\n\t ", "\r\n")),
        prop,
        cases=20,
    )
