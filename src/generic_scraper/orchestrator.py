"""Distributed execution: sharding, artifacts, and node affinity.

The real orchestrator lives outside this project. Here we define the interface
the scraper codes against and an in-process fake that the tests and the CLI's
``run`` command use. Nothing in this module touches a network or a real worker.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol

from generic_scraper.errors import ScraperError

_MEMORY_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(gb|mb|g|m)?\s*$", re.IGNORECASE)


def parse_memory_gb(text: str) -> float:
    """Turn ``"2GB"`` / ``"512MB"`` / ``"2"`` into a number of gigabytes."""

    match = _MEMORY_RE.match(text)
    if not match:
        raise ValueError(f"cannot read {text!r} as a memory size")
    amount = float(match.group(1))
    unit = (match.group(2) or "gb").lower()
    return amount / 1024 if unit in ("mb", "m") else amount


@dataclass(frozen=True)
class ResourceRequest:
    gpu: bool = False
    memory_gb: float = 0.0

    @classmethod
    def create(cls, *, gpu: bool = False, memory: str = "0") -> ResourceRequest:
        return cls(gpu=gpu, memory_gb=parse_memory_gb(memory))


@dataclass(frozen=True)
class NodeCapacity:
    name: str
    gpu: bool = False
    memory_gb: float = 0.0

    def satisfies(self, request: ResourceRequest) -> bool:
        if request.gpu and not self.gpu:
            return False
        return self.memory_gb >= request.memory_gb


@dataclass(frozen=True)
class ShardResult:
    shard: int
    node: str
    artifact: str


@dataclass(frozen=True)
class JobResult:
    shards: int
    worker_nodes: tuple[str, ...]
    shard_results: tuple[ShardResult, ...]
    placement_node: str
    uploaded: tuple[str, ...]


class ArtifactStore(Protocol):
    def upload(self, name: str) -> None:
        ...


@dataclass
class FakeArtifactStore:
    """Records uploaded artifact names in order."""

    uploaded: list[str] = field(default_factory=list)

    def upload(self, name: str) -> None:
        self.uploaded.append(name)


DEFAULT_NODE_COUNT = 8


def homogeneous_nodes(
    *, gpu: bool = False, memory_gb: float = 8.0, count: int = DEFAULT_NODE_COUNT
) -> tuple[NodeCapacity, ...]:
    """A pool of ``count`` identical worker nodes named ``node-0`` upward."""

    return tuple(
        NodeCapacity(name=f"node-{i}", gpu=gpu, memory_gb=memory_gb)
        for i in range(count)
    )


DEFAULT_NODES: tuple[NodeCapacity, ...] = homogeneous_nodes()


@dataclass
class FakeOrchestrator:
    """Schedules a sharded job across distinct fake worker nodes."""

    nodes: tuple[NodeCapacity, ...] = DEFAULT_NODES
    store: FakeArtifactStore = field(default_factory=FakeArtifactStore)

    def schedule(
        self,
        *,
        shards: int = 1,
        resources: ResourceRequest | None = None,
        artifact_name: str = "parsed_result.json",
        produce: Callable[[int, str], str] | None = None,
    ) -> JobResult:
        request = resources or ResourceRequest()
        eligible = self._eligible_nodes(request)
        needed = max(shards, 1)
        if len(eligible) < needed:
            raise ScraperError(
                "ScraperError: not enough worker nodes satisfy the resource "
                f"constraints (need {needed}, have {len(eligible)})"
            )

        chosen = eligible[:shards] if shards else eligible[:1]
        results = self._produce_shards(chosen, artifact_name, produce)
        return JobResult(
            shards=shards,
            worker_nodes=tuple(r.node for r in results),
            shard_results=results,
            placement_node=eligible[0].name,
            uploaded=tuple(self.store.uploaded),
        )

    def _eligible_nodes(self, request: ResourceRequest) -> list[NodeCapacity]:
        return [node for node in self.nodes if node.satisfies(request)]

    def _produce_shards(
        self,
        chosen: list[NodeCapacity],
        artifact_name: str,
        produce: Callable[[int, str], str] | None,
    ) -> tuple[ShardResult, ...]:
        results: list[ShardResult] = []
        for index, node in enumerate(chosen):
            name = produce(index, node.name) if produce else artifact_name
            self.store.upload(name)
            results.append(ShardResult(shard=index, node=node.name, artifact=name))
        return tuple(results)
