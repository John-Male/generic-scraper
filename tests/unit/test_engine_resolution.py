"""Unit tests for engine resolution and the fallback chain."""

from __future__ import annotations

import pytest

from generic_scraper.config import ScraperType
from generic_scraper.engines.fake_platform import FakePlatform
from generic_scraper.engines.platform import resolve_engine
from generic_scraper.errors import (
    NoEngineAvailableError,
    UnsupportedScraperEngineError,
)


def _config(**kw: object) -> ScraperType:
    return ScraperType.from_dict(dict(kw))


def test_requested_engine_is_used_when_available() -> None:
    resolved = resolve_engine(_config(scraper_engine="requests"), FakePlatform.build())

    assert resolved.engine.name == "requests"
    assert resolved.chain == ("requests",)


def test_browser_engine_is_used_when_available() -> None:
    resolved = resolve_engine(
        _config(scraper_engine="playwright", browser_type="firefox"),
        FakePlatform.build(),
    )

    assert resolved.engine.name == "playwright"


def test_unavailable_primary_falls_back_to_requests() -> None:
    resolved = resolve_engine(
        _config(scraper_engine="playwright"),
        FakePlatform.build(unavailable=["playwright"]),
    )

    assert resolved.engine.name == "requests"
    assert resolved.chain == ("playwright", "requests")


def test_start_failure_falls_back_to_configured_secondary() -> None:
    resolved = resolve_engine(
        _config(scraper_engine="selenium", secondary="requests"),
        FakePlatform.build(start_failures=["selenium"]),
    )

    assert resolved.engine.name == "requests"
    assert resolved.chain == ("selenium", "requests")


def test_unknown_engine_is_a_hard_error() -> None:
    with pytest.raises(UnsupportedScraperEngineError):
        resolve_engine(_config(scraper_engine="unknown"), FakePlatform.build())


def test_no_available_engine_raises_descriptive_error() -> None:
    with pytest.raises(NoEngineAvailableError, match="playwright, requests"):
        resolve_engine(
            _config(scraper_engine="playwright"),
            FakePlatform.build(unavailable=["playwright", "requests"]),
        )
