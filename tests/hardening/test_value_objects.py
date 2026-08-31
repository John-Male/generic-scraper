"""Immutability and default-value hardening for the frozen value objects."""

from __future__ import annotations

import dataclasses

import pytest

from generic_scraper.config import DEFAULT_ENGINE, DEFAULT_PROCESSING_TYPE, ScraperType
from generic_scraper.engines.base import FetchRequest, RawResponse
from generic_scraper.engines.platform import ResolvedEngine
from generic_scraper.engines.requests_engine import HttpResult
from generic_scraper.orchestrator import (
    JobResult,
    NodeCapacity,
    ResourceRequest,
    ShardResult,
)
from generic_scraper.parsers.base import Document
from generic_scraper.retry_policy import RetryPolicy
from generic_scraper.scraper import ScraperPlan

pytestmark = pytest.mark.hardening

FROZEN_INSTANCES = [
    ScraperType(),
    RetryPolicy(),
    Document(title=None, text="", html="", parser="regex"),
    FetchRequest(url="https://example.test"),
    RawResponse(url="https://example.test", status_code=200, html=""),
    HttpResult(status_code=200, text=""),
    ResourceRequest(),
    NodeCapacity(name="node-0"),
    ShardResult(shard=0, node="node-0", artifact="parsed_result.json"),
    JobResult(
        shards=1,
        worker_nodes=(),
        shard_results=(),
        placement_node="node-0",
        uploaded=(),
    ),
    ResolvedEngine(engine=object(), chain=()),
    ScraperPlan(
        requested_engine="requests",
        engine="requests",
        browser=None,
        processor="beautifulsoup",
        proxy=None,
        proxy_header=None,
        fallback_chain=(),
        retry_attempts=1,
        retry_backoff="exponential",
    ),
]


@pytest.mark.parametrize(
    "instance", FROZEN_INSTANCES, ids=lambda i: type(i).__name__
)
def test_value_objects_reject_mutation(instance: object) -> None:
    field_name = dataclasses.fields(instance)[0].name

    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(instance, field_name, "mutated")


def test_scrapertype_zero_arg_defaults_are_exact() -> None:
    cfg = ScraperType()

    assert cfg.scraper_engine == DEFAULT_ENGINE == "requests"
    assert cfg.browser_type is None
    assert cfg.processing_type == DEFAULT_PROCESSING_TYPE == "beautifulsoup"
    assert cfg.secondary is None
    assert cfg.use_proxy is False
    assert cfg.proxy_url is None
    assert cfg.proxy_port is None
    assert cfg.proxy_pass_key is None
    assert cfg.proxy_pass_val is None
    assert cfg.retry == RetryPolicy()
    assert cfg.retry.attempts == 1
    assert cfg.retry.backoff == "exponential"


def test_retrypolicy_zero_arg_defaults_are_exact() -> None:
    policy = RetryPolicy()

    assert policy.attempts == 1
    assert policy.backoff == "exponential"


def test_resource_and_node_defaults_are_exact() -> None:
    assert ResourceRequest() == ResourceRequest(gpu=False, memory_gb=0.0)
    assert ResourceRequest.create() == ResourceRequest(gpu=False, memory_gb=0.0)
    assert NodeCapacity(name="n") == NodeCapacity(name="n", gpu=False, memory_gb=0.0)


def test_proxy_endpoint_needs_both_the_flag_and_a_url() -> None:
    assert ScraperType(proxy_url="http://proxy.example").proxy_endpoint is None
    assert ScraperType(use_proxy=True).proxy_endpoint is None
    assert (
        ScraperType(use_proxy=True, proxy_url="http://proxy.example").proxy_endpoint
        == "http://proxy.example"
    )


def test_proxy_header_value_defaults_to_empty_string_not_a_placeholder() -> None:
    assert ScraperType(proxy_pass_key="X-Auth").proxy_header == ("X-Auth", "")


def test_unknown_scrapertype_key_error_names_the_key_exactly() -> None:
    with pytest.raises(ValueError) as excinfo:
        ScraperType.from_dict({"rotate_fingerprint": True})

    assert str(excinfo.value) == "unknown ScraperType key: 'rotate_fingerprint'"


def test_boolean_coercion_error_names_the_offending_value() -> None:
    with pytest.raises(ValueError) as excinfo:
        ScraperType.from_dict({"use_proxy": "maybe"})

    assert str(excinfo.value) == "cannot read 'maybe' as a boolean"


def test_yaml_text_error_is_prefixed_with_the_source_name() -> None:
    with pytest.raises(ValueError) as excinfo:
        ScraperType.from_yaml_text("- not\n- a mapping")
    assert str(excinfo.value) == "<yaml>: top-level YAML must be a mapping"

    with pytest.raises(ValueError) as named:
        ScraperType.from_yaml_text("- nope", source="job.yaml")
    assert str(named.value) == "job.yaml: top-level YAML must be a mapping"


def test_retry_policy_errors_are_the_exact_documented_messages() -> None:
    with pytest.raises(ValueError) as not_mapping:
        RetryPolicy.from_value("fast")
    assert str(not_mapping.value) == "retry policy must be a mapping"

    with pytest.raises(ValueError) as unknown_key:
        RetryPolicy.from_value({"jitter": 1})
    assert str(unknown_key.value) == "unknown retry policy key: 'jitter'"

    with pytest.raises(ValueError) as too_few:
        RetryPolicy.from_value({"attempts": 0})
    assert str(too_few.value) == "retry attempts must be at least 1"
