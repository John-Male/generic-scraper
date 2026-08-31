"""Hardening for FakeOrchestrator.schedule default arguments and edge shards."""

from __future__ import annotations

import pytest

from generic_scraper.orchestrator import FakeOrchestrator

pytestmark = pytest.mark.hardening


def test_schedule_defaults_to_one_shard_named_parsed_result_json() -> None:
    result = FakeOrchestrator().schedule()

    assert result.shards == 1
    assert [s.artifact for s in result.shard_results] == ["parsed_result.json"]
    assert result.uploaded == ("parsed_result.json",)


def test_schedule_with_zero_shards_still_runs_exactly_one() -> None:
    result = FakeOrchestrator().schedule(shards=0)

    assert len(result.shard_results) == 1
    assert len(result.worker_nodes) == 1
