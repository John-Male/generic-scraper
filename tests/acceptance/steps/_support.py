"""Shared helpers for the acceptance step handlers."""

from __future__ import annotations

from pathlib import Path

from generic_scraper.config import ScraperType
from generic_scraper.engines.fake_platform import FakePlatform
from generic_scraper.errors import ScraperError
from generic_scraper.scraper import Scraper
from tests.acceptance.runtime import World

_FIXTURE = Path(__file__).resolve().parents[3] / "fixtures" / "test_page.html"


def page_html() -> str:
    return _FIXTURE.read_text()


def ensure_initialized(world: World, *, force: bool = False) -> None:
    """Build the fake platform and initialise the scraper, once per execution."""

    if world.initialized and not force:
        return
    platform = FakePlatform.build(
        page_html=page_html(),
        unavailable=world.unavailable,
        start_failures=world.start_failures,
        transient_errors=world.transient_errors,
    )
    world.platform = platform
    world.scraper = Scraper(ScraperType.from_dict(world.config), platform)
    world.initialized = True
    try:
        world.scraper.initialize()
    except ScraperError as error:
        world.error = error
