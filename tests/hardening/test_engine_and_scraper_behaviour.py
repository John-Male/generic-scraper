"""Boundary and initial-state hardening for the engines and the Scraper."""

from __future__ import annotations

import pytest

from generic_scraper.config import ScraperType
from generic_scraper.engines.base import FetchRequest
from generic_scraper.engines.browser_engine import (
    BrowserEngine,
    playwright_engine,
    selenium_engine,
)
from generic_scraper.engines.fake_platform import FakeBrowserDriver, FakePlatform
from generic_scraper.engines.requests_engine import HttpResult, RequestsEngine
from generic_scraper.errors import TransientFetchError
from generic_scraper.retry import RetryRecorder
from generic_scraper.scraper import Scraper

pytestmark = pytest.mark.hardening


class _FixedStatusTransport:
    def __init__(self, status: int) -> None:
        self._status = status

    def get(
        self, url: str, headers: dict[str, str], proxy: str | None
    ) -> HttpResult:
        return HttpResult(status_code=self._status, text="body")


@pytest.mark.parametrize("status", [200, 404, 499])
def test_requests_engine_passes_through_below_500(status: int) -> None:
    response = RequestsEngine(_FixedStatusTransport(status)).fetch(
        FetchRequest(url="https://example.test")
    )

    assert response.status_code == status


@pytest.mark.parametrize("status", [500, 501, 503])
def test_requests_engine_treats_500_and_up_as_transient(status: int) -> None:
    with pytest.raises(TransientFetchError, match=f"returned {status}"):
        RequestsEngine(_FixedStatusTransport(status)).fetch(
            FetchRequest(url="https://example.test")
        )


def test_browser_engine_response_status_is_200() -> None:
    engine = BrowserEngine("playwright", "firefox", FakeBrowserDriver("<html></html>"))

    response = engine.fetch(FetchRequest(url="https://example.test"))

    assert response.status_code == 200


def test_browser_engine_defaults_an_unset_browser_type_to_chrome() -> None:
    for factory in (playwright_engine, selenium_engine):
        driver = FakeBrowserDriver("<html></html>")
        engine = factory(None, driver)
        engine.start()

        assert engine.browser_type == "chrome"
        assert engine.launched_browser == "chrome"
        assert driver.launched == "chrome"


def test_scraper_is_not_ready_before_initialize() -> None:
    scraper = Scraper(ScraperType(), FakePlatform.build(page_html="<html></html>"))

    assert scraper.ready is False
    assert scraper.fallback_chain == ()
    assert isinstance(scraper.last_retry, RetryRecorder)
    assert scraper.last_retry.attempts == 0
