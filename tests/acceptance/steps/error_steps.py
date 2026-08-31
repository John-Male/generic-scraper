"""Steps for transient-error retry behaviour."""

from __future__ import annotations

from generic_scraper.errors import FetchError
from tests.acceptance.registry import step
from tests.acceptance.runtime import World
from tests.acceptance.steps._support import ensure_initialized

_ALWAYS = 1_000_000


@step(r'a transient network error occurs during fetch')
def transient_error_during_fetch(world: World) -> None:
    world.transient_errors = _ALWAYS
    ensure_initialized(world, force=True)
    try:
        world.scraper.fetch(world.url)
    except FetchError as error:
        world.error = error
    world.retry_attempts = world.scraper.last_retry.attempts


@step(r'the Scraper should retry up to (?P<attempts>\d+) times before failing')
def should_retry_n_times(world: World, attempts: str) -> None:
    assert isinstance(world.error, FetchError), "expected the fetch to fail"
    assert world.retry_attempts == int(attempts)
