"""Unit tests for the fake orchestrator: shards, artifacts, affinity."""

from __future__ import annotations

import pytest

from generic_scraper.errors import ScraperError
from generic_scraper.orchestrator import (
    FakeArtifactStore,
    FakeOrchestrator,
    NodeCapacity,
    ResourceRequest,
    parse_memory_gb,
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [("2GB", 2.0), ("2", 2.0), ("512MB", 0.5), (" 4 gb ", 4.0)],
)
def test_parse_memory_gb(text: str, expected: float) -> None:
    assert parse_memory_gb(text) == expected


def test_parse_memory_gb_rejects_an_unreadable_size() -> None:
    with pytest.raises(ValueError, match="as a memory size"):
        parse_memory_gb("lots")


@pytest.mark.parametrize("shards", [3, 5])
def test_job_runs_on_distinct_worker_nodes(shards: int) -> None:
    result = FakeOrchestrator().schedule(shards=shards)

    assert len(result.worker_nodes) == shards
    assert len(set(result.worker_nodes)) == shards
    assert all(shard.artifact for shard in result.shard_results)


def test_each_shard_uploads_its_artifact_to_the_store() -> None:
    store = FakeArtifactStore()
    orchestrator = FakeOrchestrator(store=store)

    orchestrator.schedule(shards=3, artifact_name="parsed_result.json")

    assert store.uploaded == ["parsed_result.json"] * 3


def test_job_is_placed_on_a_node_that_satisfies_constraints() -> None:
    nodes = (
        NodeCapacity("small", gpu=False, memory_gb=1.0),
        NodeCapacity("big", gpu=False, memory_gb=4.0),
    )
    orchestrator = FakeOrchestrator(nodes=nodes)

    result = orchestrator.schedule(
        shards=1, resources=ResourceRequest.create(gpu=False, memory="2GB")
    )

    assert result.placement_node == "big"


def test_scheduling_fails_when_no_node_satisfies_constraints() -> None:
    nodes = (NodeCapacity("tiny", gpu=False, memory_gb=0.5),)

    with pytest.raises(ScraperError, match="resource constraints"):
        FakeOrchestrator(nodes=nodes).schedule(
            shards=1, resources=ResourceRequest.create(memory="2GB")
        )


def test_produce_callback_names_each_artifact() -> None:
    store = FakeArtifactStore()
    result = FakeOrchestrator(store=store).schedule(
        shards=2, produce=lambda index, node: f"{node}/parsed_result.json"
    )

    assert store.uploaded == [
        "node-0/parsed_result.json",
        "node-1/parsed_result.json",
    ]
    assert result.shard_results[1].node == "node-1"
