"""Unit tests for the Scraper: initialise, introspect, fetch, parse."""

from __future__ import annotations

from pathlib import Path

import pytest

from generic_scraper.config import ScraperType
from generic_scraper.engines.fake_platform import FakePlatform
from generic_scraper.errors import FetchError, UnsupportedScraperEngineError
from generic_scraper.scraper import Scraper

FIXTURE = Path(__file__).parents[2] / "fixtures" / "test_page.html"
PAGE_HTML = FIXTURE.read_text()


def _scraper(cfg: dict[str, object], **platform_kw: object) -> Scraper:
    platform = FakePlatform.build(page_html=PAGE_HTML, **platform_kw)
    return Scraper(ScraperType.from_dict(cfg), platform)


def test_initialize_selects_engine_and_marks_ready() -> None:
    scraper = _scraper({"scraper_engine": "requests"}).initialize()

    assert scraper.engine_name == "requests"
    assert scraper.ready is True


def test_initialize_launches_the_configured_browser() -> None:
    scraper = _scraper(
        {"scraper_engine": "selenium", "browser_type": "firefox"}
    ).initialize()

    assert scraper.engine_name == "selenium"
    assert scraper.launched_browser == "firefox"


def test_empty_config_defaults_to_requests_and_no_browser() -> None:
    scraper = _scraper({}).initialize()

    assert scraper.engine_name == "requests"
    assert scraper.launched_browser is None
    assert scraper.plan().browser is None


def test_proxy_endpoint_is_exposed_after_initialize() -> None:
    scraper = _scraper(
        {
            "use_proxy": True,
            "scraper_engine": "requests",
            "proxy_url": "http://proxy.example",
            "proxy_port": "8080",
        }
    ).initialize()

    assert scraper.plan().proxy == "http://proxy.example:8080"


def test_proxy_pass_key_becomes_a_request_header() -> None:
    scraper = _scraper(
        {
            "use_proxy": True,
            "proxy_pass_key": "X-Proxy-Auth",
            "proxy_pass_val": "dummy-token-abc",
        }
    ).initialize()

    assert scraper.request_headers == {"X-Proxy-Auth": "dummy-token-abc"}


def test_unknown_engine_fails_initialization() -> None:
    with pytest.raises(UnsupportedScraperEngineError):
        _scraper({"scraper_engine": "unknown"}).initialize()


def test_fetch_returns_a_parsed_document_with_the_title() -> None:
    scraper = _scraper(
        {"scraper_engine": "requests", "processing_type": "lxml"}
    ).initialize()

    document = scraper.fetch("https://example.com/test-page")

    assert document.parser == "lxml"
    assert document.title == "Test Page"


def test_fetch_sends_proxy_and_headers_through_the_transport() -> None:
    platform = FakePlatform.build(page_html=PAGE_HTML)
    scraper = Scraper(
        ScraperType.from_dict(
            {
                "use_proxy": True,
                "proxy_url": "http://proxy.example",
                "proxy_port": "3128",
                "proxy_pass_key": "X-Auth-Token",
                "proxy_pass_val": "dummy-token-xyz",
            }
        ),
        platform,
    ).initialize()

    scraper.fetch("https://example.com/test-page")

    call = platform.transport.calls[-1]
    assert call.proxy == "http://proxy.example:3128"
    assert call.headers["X-Auth-Token"] == "dummy-token-xyz"


def test_fetch_retries_transient_errors_up_to_the_policy_limit() -> None:
    scraper = _scraper(
        {"scraper_engine": "requests", "retry": {"attempts": 3}},
        transient_errors=9,
    ).initialize()

    with pytest.raises(FetchError, match="3 attempt"):
        scraper.fetch("https://example.com/test-page")

    assert scraper.last_retry.attempts == 3


def test_fetch_recovers_when_transient_errors_clear_before_the_limit() -> None:
    scraper = _scraper(
        {"scraper_engine": "requests", "retry": {"attempts": 5}},
        transient_errors=2,
    ).initialize()

    document = scraper.fetch("https://example.com/test-page")

    assert document.title == "Test Page"
    assert scraper.last_retry.attempts == 3
