"""Steps that fetch a page and assert on the parsed document."""

from __future__ import annotations

from tests.acceptance.registry import StepError, step
from tests.acceptance.runtime import World
from tests.acceptance.steps._support import ensure_initialized


@step(r'I fetch the test URL')
def fetch_the_test_url(world: World) -> None:
    ensure_initialized(world)
    if world.error is not None:
        raise StepError(f"initialisation failed: {world.error}")
    world.document = world.scraper.fetch(world.url)


@step(r'the Scraper should return a parsed document using "(?P<processor>[^"]+)"')
def should_return_parsed_document(world: World, processor: str) -> None:
    assert world.document is not None, "no document was fetched"
    assert world.document.parser == processor


@step(r'the parsed document should contain the page title')
def document_should_contain_title(world: World) -> None:
    assert world.document is not None, "no document was fetched"
    assert world.document.title == "Test Page"
