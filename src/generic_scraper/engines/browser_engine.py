"""Browser-backed engines: Playwright and Selenium.

Both engines drive a real browser in production and a fake :class:`BrowserDriver`
in tests. The engine records which browser it launched so callers can assert on
worker-node behaviour without a real browser.
"""

from __future__ import annotations

from typing import Protocol

from generic_scraper.engines.base import (
    PLAYWRIGHT,
    SELENIUM,
    FetchRequest,
    RawResponse,
)


class BrowserDriver(Protocol):
    """Launches a browser and returns rendered page source."""

    def launch(self, browser_type: str, proxy: str | None) -> None:
        ...

    def page_source(self, url: str, headers: dict[str, str]) -> str:
        ...

    def close(self) -> None:
        ...


class BrowserEngine:
    """A scraping engine that renders pages in a launched browser."""

    def __init__(
        self, name: str, browser_type: str | None, driver: BrowserDriver
    ) -> None:
        self.name = name
        self.browser_type = browser_type or "chrome"
        self._driver = driver
        self.launched_browser: str | None = None

    def start(self, proxy: str | None = None) -> None:
        self._driver.launch(self.browser_type, proxy)
        self.launched_browser = self.browser_type

    def fetch(self, request: FetchRequest) -> RawResponse:
        if self.launched_browser is None:
            self.start(request.proxy)
        html = self._driver.page_source(request.url, dict(request.headers))
        return RawResponse(
            url=request.url,
            status_code=200,
            html=html,
            request_headers=dict(request.headers),
        )


def playwright_engine(browser_type: str | None, driver: BrowserDriver) -> BrowserEngine:
    return BrowserEngine(PLAYWRIGHT, browser_type, driver)


def selenium_engine(browser_type: str | None, driver: BrowserDriver) -> BrowserEngine:
    return BrowserEngine(SELENIUM, browser_type, driver)
