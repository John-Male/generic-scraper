"""Unit tests for the engine adapters at their driver/transport boundary."""

from __future__ import annotations

import pytest

from generic_scraper.engines.base import FetchRequest
from generic_scraper.engines.browser_engine import BrowserEngine
from generic_scraper.engines.fake_platform import FakeBrowserDriver, FakeHttpTransport
from generic_scraper.engines.requests_engine import HttpResult, RequestsEngine
from generic_scraper.errors import TransientFetchError


class _Status500Transport:
    def get(
        self, url: str, headers: dict[str, str], proxy: str | None
    ) -> HttpResult:
        return HttpResult(status_code=503, text="upstream is down")


def test_requests_engine_turns_a_5xx_into_a_transient_error() -> None:
    engine = RequestsEngine(_Status500Transport())

    with pytest.raises(TransientFetchError, match="returned 503"):
        engine.fetch(FetchRequest(url="https://example.com"))


def test_requests_engine_returns_the_body_on_success() -> None:
    engine = RequestsEngine(FakeHttpTransport("<title>ok</title>"))

    response = engine.fetch(FetchRequest(url="https://example.com"))

    assert response.status_code == 200
    assert response.html == "<title>ok</title>"


def test_browser_engine_fetch_launches_the_browser_on_first_use() -> None:
    engine = BrowserEngine("playwright", "chrome", FakeBrowserDriver("<html></html>"))

    response = engine.fetch(FetchRequest(url="https://example.com"))

    assert engine.launched_browser == "chrome"
    assert response.html == "<html></html>"


def test_fake_browser_driver_close_is_a_noop() -> None:
    driver = FakeBrowserDriver("<html></html>")
    driver.launch("chrome", None)

    assert driver.close() is None
