"""The Scraper: high-level policy tying configuration to engine and parser.

This module is deliberately far from IO. It depends on the engine *platform*
interface and the parser registry, never on ``requests``, Playwright, Selenium,
or a filesystem.
"""

from __future__ import annotations

from dataclasses import dataclass

from generic_scraper.config import ScraperType
from generic_scraper.engines.base import BROWSER_ENGINES, Engine, FetchRequest
from generic_scraper.engines.browser_engine import BrowserEngine
from generic_scraper.engines.platform import EnginePlatform, resolve_engine
from generic_scraper.errors import ScraperError
from generic_scraper.parsers.base import Document, Parser
from generic_scraper.parsers.registry import create_parser
from generic_scraper.retry import RetryRecorder, Sleeper, call_with_retry, no_sleep


@dataclass(frozen=True)
class ScraperPlan:
    """A resolved, read-only summary of how the scraper is configured."""

    requested_engine: str
    engine: str
    browser: str | None
    processor: str
    proxy: str | None
    proxy_header: str | None
    fallback_chain: tuple[str, ...]
    retry_attempts: int
    retry_backoff: str


class Scraper:
    """Resolves an engine and parser for a :class:`ScraperType`, then fetches."""

    def __init__(
        self,
        config: ScraperType,
        platform: EnginePlatform,
        *,
        sleep: Sleeper = no_sleep,
    ) -> None:
        self._config = config
        self._platform = platform
        self._sleep = sleep
        self._engine: Engine | None = None
        self._parser: Parser | None = None
        self._chain: tuple[str, ...] = ()
        self.ready = False
        self.last_retry = RetryRecorder()

    # -- initialisation ----------------------------------------------------

    def initialize(self) -> Scraper:
        resolved = resolve_engine(self._config, self._platform)
        engine = resolved.engine
        if isinstance(engine, BrowserEngine) and engine.launched_browser is None:
            engine.start(self._config.proxy_endpoint)
        self._engine = engine
        self._chain = resolved.chain
        self._parser = create_parser(self._config.processing_type)
        self.ready = True
        return self

    # -- introspection ---------------------------------------------------

    @property
    def engine_name(self) -> str:
        return self._require_engine().name

    @property
    def parser_name(self) -> str:
        return self._require_parser().name

    @property
    def fallback_chain(self) -> tuple[str, ...]:
        return self._chain

    @property
    def launched_browser(self) -> str | None:
        engine = self._require_engine()
        return getattr(engine, "launched_browser", None)

    @property
    def request_headers(self) -> dict[str, str]:
        pair = self._config.proxy_header
        return {pair[0]: pair[1]} if pair is not None else {}

    def plan(self) -> ScraperPlan:
        cfg = self._config
        header = cfg.proxy_header
        browser = self.launched_browser if self.engine_name in BROWSER_ENGINES else None
        return ScraperPlan(
            requested_engine=cfg.scraper_engine,
            engine=self.engine_name,
            browser=browser,
            processor=self.parser_name,
            proxy=cfg.proxy_endpoint,
            proxy_header=f"{header[0]}: {header[1]}" if header else None,
            fallback_chain=self._chain,
            retry_attempts=cfg.retry.attempts,
            retry_backoff=cfg.retry.backoff,
        )

    # -- fetching -------------------------------------------------------

    def fetch(self, url: str) -> Document:
        engine = self._require_engine()
        parser = self._require_parser()
        request = FetchRequest(
            url=url,
            headers=self.request_headers,
            proxy=self._config.proxy_endpoint,
        )
        self.last_retry = RetryRecorder()
        response = call_with_retry(
            lambda: engine.fetch(request),
            self._config.retry,
            sleep=self._sleep,
            recorder=self.last_retry,
        )
        return parser.parse(response.html)

    # -- internals -----------------------------------------------------

    def _require_engine(self) -> Engine:
        if self._engine is None:
            raise ScraperError("scraper is not initialised; call initialize() first")
        return self._engine

    def _require_parser(self) -> Parser:
        if self._parser is None:
            raise ScraperError("scraper is not initialised; call initialize() first")
        return self._parser
