"""Engine resolution policy and the platform boundary it depends on.

The *platform* is the worker node's view of which engines can run and how to
start them. It is an interface owned here (high-level policy) so that the live
implementation and the test fake both depend inward on this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from generic_scraper.config import ScraperType
from generic_scraper.engines.base import KNOWN_ENGINES, REQUESTS, Engine
from generic_scraper.errors import (
    NoEngineAvailableError,
    UnsupportedScraperEngineError,
)


class EngineStartError(Exception):
    """Raised by a platform when a known, available engine will not start."""


class EnginePlatform(Protocol):
    """A worker node's ability to run scraping engines."""

    def available(self, name: str) -> bool:
        """Whether engine ``name`` can run on this node at all."""
        ...

    def create(self, name: str, config: ScraperType) -> Engine:
        """Build and start engine ``name``. Raises :class:`EngineStartError`."""
        ...


@dataclass(frozen=True)
class ResolvedEngine:
    """The engine that will be used, plus the chain that led to it."""

    engine: Engine
    chain: tuple[str, ...]


def resolve_engine(config: ScraperType, platform: EnginePlatform) -> ResolvedEngine:
    """Pick an engine for ``config``, falling back when the primary cannot run.

    The primary engine name must be one this package knows; an unknown name is a
    hard error. A known primary that is unavailable or fails to start falls back
    to the configured ``secondary`` and then to ``requests``.
    """

    primary = config.scraper_engine
    if primary not in KNOWN_ENGINES:
        raise UnsupportedScraperEngineError(
            f"UnsupportedScraperEngineError: {primary!r} is not a supported "
            f"scraper engine; choose one of {', '.join(KNOWN_ENGINES)}"
        )

    tried: list[str] = []
    for name in _candidate_chain(config):
        if name in tried:
            continue
        tried.append(name)
        if not platform.available(name):
            continue
        try:
            engine = platform.create(name, config)
        except EngineStartError:
            continue
        return ResolvedEngine(engine=engine, chain=tuple(tried))

    raise NoEngineAvailableError(
        "NoEngineAvailableError: no scraping engine could be started; tried "
        + ", ".join(tried)
    )


def _candidate_chain(config: ScraperType) -> list[str]:
    chain = [config.scraper_engine]
    if config.secondary:
        chain.append(config.secondary)
    if REQUESTS not in chain:
        chain.append(REQUESTS)
    return chain
