"""Steps that initialise the Scraper and assert on the resolved engine/parser."""

from __future__ import annotations

from tests.acceptance.registry import StepError, step
from tests.acceptance.runtime import World
from tests.acceptance.steps._support import ensure_initialized


@step(r'I initialize the Scraper(?: on .+)?')
def initialize_the_scraper(world: World) -> None:
    ensure_initialized(world, force=True)


def _scraper(world: World):
    if world.error is not None:
        raise StepError(f"initialisation failed: {world.error}")
    if world.scraper is None or not world.scraper.ready:
        raise StepError("scraper was never initialised")
    return world.scraper


@step(r'the Scraper should use the "(?P<engine>[^"]+)" engine')
def should_use_engine(world: World, engine: str) -> None:
    assert _scraper(world).engine_name == engine


@step(r'the Scraper should be ready to fetch pages')
def should_be_ready(world: World) -> None:
    assert _scraper(world).ready is True


@step(r'the Scraper should launch "(?P<browser>[^"]+)" for "(?P<engine>[^"]+)"')
def should_launch_browser(world: World, browser: str, engine: str) -> None:
    scraper = _scraper(world)
    assert scraper.engine_name == engine
    assert scraper.launched_browser == browser


@step(r'the Scraper should use "(?P<engine>[^"]+)" as the default scraper engine')
def should_use_default_engine(world: World, engine: str) -> None:
    assert _scraper(world).engine_name == engine


@step(r'the Scraper should have no browser configured')
def should_have_no_browser(world: World) -> None:
    scraper = _scraper(world)
    assert scraper.launched_browser is None
    assert scraper.plan().browser is None


@step(r'the Scraper should fall back to "(?P<engine>[^"]+)"')
def should_fall_back(world: World, engine: str) -> None:
    assert _scraper(world).engine_name == engine


@step(r'the Scraper should use "(?P<processor>[^"]+)" to parse HTML responses')
def should_use_processor(world: World, processor: str) -> None:
    assert _scraper(world).parser_name == processor


@step(r'the Scraper should attempt to use "(?P<engine>[^"]+)" as the secondary engine')
def should_use_secondary(world: World, engine: str) -> None:
    scraper = _scraper(world)
    assert scraper.engine_name == engine
    assert len(scraper.fallback_chain) > 1


@step(r'the initialization should succeed')
def initialization_should_succeed(world: World) -> None:
    assert world.error is None
    assert world.scraper is not None and world.scraper.ready is True


@step(r'the Scraper initialization should fail with "(?P<error>[^"]+)"')
def initialization_should_fail(world: World, error: str) -> None:
    assert world.error is not None, "expected initialisation to fail"
    assert type(world.error).__name__ == error


@step(
    r'the Scraper should configure the HTTP client to use the proxy '
    r'"(?P<endpoint>[^"]+)"'
)
def should_configure_proxy(world: World, endpoint: str) -> None:
    assert _scraper(world).plan().proxy == endpoint


@step(
    r'the Scraper should include header '
    r'"(?P<key>[^"]+): (?P<value>[^"]+)" on proxied requests'
)
def should_include_header(world: World, key: str, value: str) -> None:
    assert _scraper(world).request_headers.get(key) == value
