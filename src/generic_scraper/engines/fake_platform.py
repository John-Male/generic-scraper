"""An in-process engine platform with no network and no real browser.

This is the platform the test suite and the CLI's QA affordances run against. It
serves a caller-supplied HTML body for every fetch and records what each engine
was asked to do, so behaviour can be asserted without touching the internet.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from generic_scraper.config import ScraperType
from generic_scraper.engines.base import (
    PLAYWRIGHT,
    REQUESTS,
    SELENIUM,
    Engine,
)
from generic_scraper.engines.browser_engine import (
    BrowserEngine,
    playwright_engine,
    selenium_engine,
)
from generic_scraper.engines.platform import EngineStartError
from generic_scraper.engines.requests_engine import HttpResult, RequestsEngine
from generic_scraper.errors import TransientFetchError


@dataclass
class RecordedRequest:
    url: str
    headers: dict[str, str]
    proxy: str | None


class FakeHttpTransport:
    """Serves canned HTML and can fail the first few attempts transiently."""

    def __init__(self, html: str, transient_errors: int = 0) -> None:
        self._html = html
        self._remaining_errors = transient_errors
        self.calls: list[RecordedRequest] = []

    def get(
        self, url: str, headers: dict[str, str], proxy: str | None
    ) -> HttpResult:
        self.calls.append(RecordedRequest(url, dict(headers), proxy))
        if self._remaining_errors > 0:
            self._remaining_errors -= 1
            raise TransientFetchError(
                f"TransientFetchError: transient network error fetching {url}"
            )
        return HttpResult(status_code=200, text=self._html)


class FakeBrowserDriver:
    """Records launches and navigations; never starts a browser."""

    def __init__(self, html: str) -> None:
        self._html = html
        self.launched: str | None = None
        self.navigations: list[RecordedRequest] = []

    def launch(self, browser_type: str, proxy: str | None) -> None:
        self.launched = browser_type

    def page_source(self, url: str, headers: dict[str, str]) -> str:
        self.navigations.append(RecordedRequest(url, dict(headers), None))
        return self._html

    def close(self) -> None:
        return None


@dataclass
class FakePlatform:
    """A worker node whose engines are all fakes."""

    page_html: str = ""
    unavailable: frozenset[str] = field(default_factory=frozenset)
    start_failures: frozenset[str] = field(default_factory=frozenset)
    transient_errors: int = 0

    def __post_init__(self) -> None:
        self.transport = FakeHttpTransport(self.page_html, self.transient_errors)
        self.drivers: list[FakeBrowserDriver] = []
        self.created: list[str] = []

    @classmethod
    def build(
        cls,
        *,
        page_html: str = "",
        unavailable: Iterable[str] = (),
        start_failures: Iterable[str] = (),
        transient_errors: int = 0,
    ) -> FakePlatform:
        return cls(
            page_html=page_html,
            unavailable=frozenset(unavailable),
            start_failures=frozenset(start_failures),
            transient_errors=transient_errors,
        )

    def available(self, name: str) -> bool:
        return name not in self.unavailable

    def create(self, name: str, config: ScraperType) -> Engine:
        if name in self.start_failures:
            raise EngineStartError(f"{name} failed to start on the worker")
        self.created.append(name)
        if name == REQUESTS:
            return RequestsEngine(self.transport)
        if name in (PLAYWRIGHT, SELENIUM):
            driver = FakeBrowserDriver(self.page_html)
            self.drivers.append(driver)
            factory = playwright_engine if name == PLAYWRIGHT else selenium_engine
            engine: BrowserEngine = factory(config.browser_type, driver)
            return engine
        raise EngineStartError(f"{name} is not a known engine")
