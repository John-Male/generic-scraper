"""Steps that build up the ScraperType configuration and worker conditions."""

from __future__ import annotations

from tests.acceptance.registry import step
from tests.acceptance.runtime import World


@step(r'default scraper configuration exists')
def default_configuration_exists(world: World) -> None:
    world.config.setdefault("scraper_engine", "requests")


@step(r'I have an empty ScraperType configuration')
def empty_configuration(world: World) -> None:
    world.config.clear()


@step(
    r'(?:I have a |a )ScraperType configuration with '
    r'"(?P<key>[^"]+)" set to "(?P<value>[^"]*)"'
)
def configuration_with_key(world: World, key: str, value: str) -> None:
    world.config[key] = value


@step(r'"(?P<key>[^"]+)" set to "(?P<value>[^"]*)"')
def also_set_key(world: World, key: str, value: str) -> None:
    world.config[key] = value


@step(r'"(?P<engine>[^"]+)" is not available on the worker node')
def engine_not_available(world: World, engine: str) -> None:
    world.unavailable.add(engine)


@step(r'"(?P<engine>[^"]+)" fails to start on the worker')
def engine_fails_to_start(world: World, engine: str) -> None:
    world.start_failures.add(engine)


@step(r'retry policy set to (?P<attempts>\d+) attempts with exponential backoff')
def retry_policy(world: World, attempts: str) -> None:
    world.config["retry"] = {"attempts": int(attempts), "backoff": "exponential"}


@step(r'a test URL "(?P<url>[^"]+)"')
def a_test_url(world: World, url: str) -> None:
    world.url = url
