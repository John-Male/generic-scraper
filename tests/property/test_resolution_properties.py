"""Property tests for engine resolution and the fallback chain."""

from __future__ import annotations

import random

import pytest

from generic_scraper.config import ScraperType
from generic_scraper.engines.base import KNOWN_ENGINES
from generic_scraper.engines.fake_platform import FakePlatform
from generic_scraper.engines.platform import resolve_engine
from generic_scraper.errors import NoEngineAvailableError
from tests.property.framework import for_all

pytestmark = pytest.mark.property

_ALL = list(KNOWN_ENGINES)


def _case(rng: random.Random) -> tuple[ScraperType, FakePlatform]:
    primary = rng.choice(_ALL)
    config: dict[str, object] = {"scraper_engine": primary}
    if rng.random() < 0.6:
        config["secondary"] = rng.choice([*_ALL, "bogus"])
    broken = {
        name for name in _ALL if rng.random() < 0.4
    }
    unavailable = {name for name in broken if rng.random() < 0.5}
    start_failures = broken - unavailable
    platform = FakePlatform.build(
        unavailable=unavailable, start_failures=start_failures
    )
    return ScraperType.from_dict(config), platform


def _candidate_chain(config: ScraperType) -> list[str]:
    chain = [config.scraper_engine]
    if config.secondary:
        chain.append(config.secondary)
    if "requests" not in chain:
        chain.append("requests")
    return chain


def _usable(name: str, platform: FakePlatform) -> bool:
    return (
        name in KNOWN_ENGINES
        and platform.available(name)
        and name not in platform.start_failures
    )


def test_resolution_ends_on_a_usable_engine_or_raises_cleanly() -> None:
    def prop(case: tuple[ScraperType, FakePlatform]) -> None:
        config, platform = case
        any_usable = any(
            _usable(name, platform) for name in _candidate_chain(config)
        )
        if not any_usable:
            with pytest.raises(NoEngineAvailableError):
                resolve_engine(config, platform)
            return

        resolved = resolve_engine(config, platform)
        assert resolved.engine.name == resolved.chain[-1]
        assert platform.available(resolved.engine.name)
        # the chain never repeats a candidate
        assert len(resolved.chain) == len(set(resolved.chain))
        # every earlier candidate was genuinely unusable
        for skipped in resolved.chain[:-1]:
            assert not _usable(skipped, platform)

    for_all(_case, prop, cases=200)


def test_failure_is_only_reported_after_trying_requests() -> None:
    def prop(case: tuple[ScraperType, FakePlatform]) -> None:
        config, platform = case
        try:
            resolve_engine(config, platform)
        except NoEngineAvailableError as error:
            # requests is the built-in last resort; a clean failure must name it
            assert "requests" in str(error)

    for_all(_case, prop, cases=200)


def test_resolution_is_deterministic() -> None:
    def prop(case: tuple[ScraperType, FakePlatform]) -> None:
        config, _platform = case
        a = FakePlatform.build(unavailable={"playwright"})
        b = FakePlatform.build(unavailable={"playwright"})
        first = resolve_engine(config, a)
        second = resolve_engine(config, b)
        assert first.chain == second.chain
        assert first.engine.name == second.engine.name

    for_all(_case, prop, cases=100)
