"""Property tests for memory parsing, node affinity, and sharding."""

from __future__ import annotations

import math
import random

import pytest

from generic_scraper.errors import ScraperError
from generic_scraper.orchestrator import (
    FakeArtifactStore,
    FakeOrchestrator,
    NodeCapacity,
    ResourceRequest,
    homogeneous_nodes,
    parse_memory_gb,
)
from tests.property.framework import for_all

pytestmark = pytest.mark.property


def _amount(rng: random.Random) -> float:
    return round(rng.uniform(0.1, 4096), rng.randint(0, 3))


def test_memory_units_scale_as_documented() -> None:
    def prop(amount: float) -> None:
        assert parse_memory_gb(f"{amount}GB") == pytest.approx(amount)
        assert parse_memory_gb(f"{amount}") == pytest.approx(amount)
        assert parse_memory_gb(f"{amount}MB") == pytest.approx(amount / 1024)

    for_all(_amount, prop)


def test_memory_parsing_ignores_surrounding_space_and_case() -> None:
    def prop(amount: float) -> None:
        canonical = parse_memory_gb(f"{amount}GB")
        assert parse_memory_gb(f"  {amount} gb ") == pytest.approx(canonical)
        assert parse_memory_gb(f"{amount}Gb") == pytest.approx(canonical)

    for_all(_amount, prop)


def _request(rng: random.Random) -> ResourceRequest:
    return ResourceRequest(
        gpu=rng.random() < 0.5, memory_gb=round(rng.uniform(0, 16), 2)
    )


def test_node_satisfaction_is_monotonic_in_capacity() -> None:
    def prop(request: ResourceRequest) -> None:
        weak = NodeCapacity("weak", gpu=request.gpu, memory_gb=request.memory_gb)
        strong = NodeCapacity(
            "strong", gpu=True, memory_gb=request.memory_gb + 8
        )
        assert weak.satisfies(request)
        assert strong.satisfies(request)
        starved = NodeCapacity(
            "starved", gpu=request.gpu, memory_gb=max(request.memory_gb - 1, -1)
        )
        if request.memory_gb > 0:
            assert not starved.satisfies(request)

    for_all(_request, prop)


def test_gpu_request_is_never_met_by_a_cpu_node() -> None:
    def prop(memory_gb: float) -> None:
        node = NodeCapacity("cpu", gpu=False, memory_gb=memory_gb + 100)
        assert not node.satisfies(ResourceRequest(gpu=True, memory_gb=memory_gb))

    for_all(lambda rng: round(rng.uniform(0, 32), 2), prop)


def test_every_shard_lands_on_a_distinct_node_and_uploads_once() -> None:
    def prop(shards: int) -> None:
        store = FakeArtifactStore()
        result = FakeOrchestrator(
            nodes=homogeneous_nodes(count=8), store=store
        ).schedule(shards=shards)
        assert len(result.worker_nodes) == shards
        assert len(set(result.worker_nodes)) == shards
        assert len(store.uploaded) == shards
        assert [s.shard for s in result.shard_results] == list(range(shards))
        assert result.placement_node in result.worker_nodes

    for_all(lambda rng: rng.randint(1, 8), prop, cases=40)


def test_scheduling_needs_one_eligible_node_per_shard() -> None:
    def prop(params: tuple[int, int]) -> None:
        shards, eligible = params
        nodes = homogeneous_nodes(count=eligible, memory_gb=8.0)
        orchestrator = FakeOrchestrator(nodes=nodes, store=FakeArtifactStore())
        request = ResourceRequest(memory_gb=4.0)
        if eligible >= shards:
            result = orchestrator.schedule(shards=shards, resources=request)
            assert len(result.worker_nodes) == shards
        else:
            with pytest.raises(ScraperError, match="resource constraints"):
                orchestrator.schedule(shards=shards, resources=request)

    def strategy(rng: random.Random) -> tuple[int, int]:
        return rng.randint(1, 6), rng.randint(0, 6)

    for_all(strategy, prop, cases=40)


def test_parsed_amounts_are_finite_and_non_negative() -> None:
    def prop(amount: float) -> None:
        parsed = parse_memory_gb(f"{amount}MB")
        assert math.isfinite(parsed)
        assert parsed >= 0

    for_all(_amount, prop)
