"""Parser title/text extraction hardening.

The unit suite parses one tidy page. These cases use markup that is messy in
the ways the parsers actually guard against: mixed-case tags, runs of
whitespace, ``<script>``/``<style>`` blocks with text on either side, nested
markup inside a script, and a stray closing tag.
"""

from __future__ import annotations

import pytest

from generic_scraper.parsers.base import KNOWN_PROCESSING_TYPES
from generic_scraper.parsers.registry import create_parser

pytestmark = pytest.mark.hardening

HARDENING_PAGE = """<!DOCTYPE html>
<HTML><head>
<TITLE>Weekly   Report
Digest</TITLE>
</head>
<body>
<div>lead-in</div>
<h1>headline one</h1>
<p>alpha    beta</p>
<SCRIPT>var leaked = "SCRIPT_TOKEN";</SCRIPT>
<p>gamma delta</p>
<style>.c { content: "STYLE_TOKEN" }</style>
<p>epsilon zeta</p>
<script>outerJS<span>NESTED_TOKEN</span>tailJS</script>
<p>final-line</p>
</body></HTML>"""

PRESENT = ["lead-in", "headline one", "alpha beta", "gamma delta", "epsilon zeta",
           "final-line"]
ABSENT = ["SCRIPT_TOKEN", "STYLE_TOKEN", "NESTED_TOKEN", "outerJS", "tailJS",
          "<", ">", "XX"]


@pytest.mark.parametrize("name", KNOWN_PROCESSING_TYPES)
def test_title_whitespace_is_collapsed_regardless_of_tag_case(name: str) -> None:
    document = create_parser(name).parse(HARDENING_PAGE)

    assert document.title == "Weekly Report Digest"
    assert document.parser == name


@pytest.mark.parametrize("name", KNOWN_PROCESSING_TYPES)
def test_visible_text_survives_around_script_and_style_blocks(name: str) -> None:
    text = create_parser(name).parse(HARDENING_PAGE).text

    for fragment in PRESENT:
        assert fragment in text, f"{name}: expected {fragment!r} in {text!r}"


@pytest.mark.parametrize("name", KNOWN_PROCESSING_TYPES)
def test_markup_and_script_content_never_leak_into_text(name: str) -> None:
    text = create_parser(name).parse(HARDENING_PAGE).text

    for fragment in ABSENT:
        assert fragment not in text, f"{name}: {fragment!r} leaked into {text!r}"


def test_html_parser_joins_title_fragments_without_a_separator() -> None:
    document = create_parser("html.parser").parse(
        "<title>Weekly <b>Report</b> Digest</title><body><p>body</p></body>"
    )

    assert document.title == "Weekly Report Digest"


def test_html_parser_recovers_from_a_stray_closing_script_tag() -> None:
    document = create_parser("html.parser").parse(
        "<body><p>before</p></script><p>after</p></body>"
    )

    assert "before" in document.text
    assert "after" in document.text
