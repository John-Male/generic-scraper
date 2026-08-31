"""Hardening for error messages and the runtime-checkable parser contract.

The domain model requires an error that *names what was tried*. These tests pin
the parts of each message a job log depends on: the leading class name and the
list of names that were considered.
"""

from __future__ import annotations

import pytest

from generic_scraper.config import ScraperType
from generic_scraper.engines.fake_platform import FakePlatform
from generic_scraper.engines.platform import resolve_engine
from generic_scraper.errors import (
    FetchError,
    NoEngineAvailableError,
    TransientFetchError,
    UnsupportedProcessingTypeError,
    UnsupportedScraperEngineError,
)
from generic_scraper.parsers.base import Parser
from generic_scraper.parsers.registry import create_parser
from generic_scraper.retry import call_with_retry
from generic_scraper.retry_policy import RetryPolicy

pytestmark = pytest.mark.hardening


def test_unknown_engine_error_names_class_and_every_known_engine() -> None:
    with pytest.raises(UnsupportedScraperEngineError) as excinfo:
        resolve_engine(ScraperType(scraper_engine="curl"), FakePlatform.build())

    assert str(excinfo.value) == (
        "UnsupportedScraperEngineError: 'curl' is not a supported scraper "
        "engine; choose one of requests, playwright, selenium"
    )


def test_no_engine_available_error_lists_what_was_tried() -> None:
    platform = FakePlatform.build(unavailable=["requests", "playwright", "selenium"])

    with pytest.raises(NoEngineAvailableError) as excinfo:
        resolve_engine(ScraperType(secondary="playwright"), platform)

    assert str(excinfo.value) == (
        "NoEngineAvailableError: no scraping engine could be started; "
        "tried requests, playwright"
    )


def test_unknown_processing_type_error_names_class_and_every_choice() -> None:
    with pytest.raises(UnsupportedProcessingTypeError) as excinfo:
        create_parser("xhtml")

    assert str(excinfo.value) == (
        "UnsupportedProcessingTypeError: 'xhtml' is not a supported processing "
        "type; choose one of beautifulsoup, lxml, html.parser, regex"
    )


def test_fetch_error_message_carries_the_last_transient_error() -> None:
    def always_fails() -> str:
        raise TransientFetchError("TransientFetchError: upstream 503 from edge")

    with pytest.raises(FetchError) as excinfo:
        call_with_retry(
            always_fails,
            RetryPolicy(attempts=2, backoff="none"),
            sleep=lambda _s: None,
        )

    message = str(excinfo.value)
    assert message.startswith("FetchError: fetch failed after 2 attempt(s): ")
    assert "upstream 503 from edge" in message


def test_parser_is_a_runtime_checkable_contract() -> None:
    assert isinstance(create_parser("regex"), Parser)
    assert not isinstance(object(), Parser)
