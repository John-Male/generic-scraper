"""Steps for distributed execution, artifact upload, and node affinity."""

from __future__ import annotations

from generic_scraper.config import ScraperType
from generic_scraper.engines.fake_platform import FakePlatform
from generic_scraper.orchestrator import (
    DEFAULT_NODES,
    FakeArtifactStore,
    FakeOrchestrator,
    ResourceRequest,
)
from generic_scraper.scraper import Scraper
from tests.acceptance.registry import step
from tests.acceptance.runtime import World
from tests.acceptance.steps._support import page_html


@step(r'the job is configured to run with (?P<shards>\d+) parallel shards')
def job_with_shards(world: World, shards: str) -> None:
    world.shards = int(shards)


@step(r'the job requests GPU (?P<gpu>\w+) and memory (?P<memory>\S+)')
def job_requests_resources(world: World, gpu: str, memory: str) -> None:
    world.resources = ResourceRequest.create(
        gpu=gpu.strip().lower() == "true", memory=memory
    )


@step(r'a worker produced "(?P<artifact>[^"]+)"')
def a_worker_produced(world: World, artifact: str) -> None:
    world.artifact = artifact


@step(r'the orchestrator schedules the job')
def orchestrator_schedules_job(world: World) -> None:
    store = FakeArtifactStore()
    world.store = store
    orchestrator = FakeOrchestrator(nodes=DEFAULT_NODES, store=store)
    titles: list[str | None] = []

    def produce(index: int, node: str) -> str:
        scraper = Scraper(
            ScraperType.from_dict(world.config),
            FakePlatform.build(page_html=page_html()),
        ).initialize()
        titles.append(scraper.fetch(world.url).title)
        return "parsed_result.json"

    world.job = orchestrator.schedule(
        shards=world.shards, resources=world.resources, produce=produce
    )
    world.parsed_titles = titles


@step(r'the worker finishes the shard')
def worker_finishes_shard(world: World) -> None:
    store = FakeArtifactStore()
    world.store = store
    orchestrator = FakeOrchestrator(nodes=DEFAULT_NODES, store=store)
    world.job = orchestrator.schedule(
        shards=1, artifact_name=world.artifact or "parsed_result.json"
    )


@step(r'the job should run on (?P<shards>\d+) distinct worker nodes')
def job_runs_on_distinct_nodes(world: World, shards: str) -> None:
    assert len(set(world.job.worker_nodes)) == int(shards)


@step(r'each worker should produce a parsed artifact')
def each_worker_produces_artifact(world: World) -> None:
    assert len(world.job.shard_results) == world.shards
    assert all(shard.artifact for shard in world.job.shard_results)
    assert world.parsed_titles == ["Test Page"] * world.shards


@step(
    r'the artifact "(?P<artifact>[^"]+)" should be uploaded to the job artifact store'
)
def artifact_uploaded(world: World, artifact: str) -> None:
    assert artifact in world.store.uploaded


@step(r'the job should be placed on a node that satisfies the resource constraints')
def job_placed_on_satisfying_node(world: World) -> None:
    request = world.resources or ResourceRequest()
    node = next(n for n in DEFAULT_NODES if n.name == world.job.placement_node)
    assert node.satisfies(request)
