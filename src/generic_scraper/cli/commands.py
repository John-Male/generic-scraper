"""The three CLI command handlers: ``describe``, ``fetch``, and ``run``.

Each takes the parsed argparse namespace and returns the JSON-serialisable
dict that :func:`generic_scraper.cli.main` prints.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from generic_scraper.cli.support import (
    REDACTED,
    build_scraper,
    load_config,
    parse_kv,
    parse_nodes,
    publish_uploads,
    redact_header,
    to_bool,
    write_shard_summary,
)
from generic_scraper.errors import ScraperError
from generic_scraper.orchestrator import (
    FakeArtifactStore,
    FakeOrchestrator,
    ResourceRequest,
)


def describe(args: argparse.Namespace) -> dict[str, object]:
    config = load_config(args.config)
    plan = build_scraper(config, args).initialize().plan()
    return {
        "engine": plan.engine,
        "requested_engine": plan.requested_engine,
        "browser": plan.browser,
        "processor": plan.processor,
        "proxy": plan.proxy,
        "proxy_header": redact_header(plan.proxy_header),
        "fallback_chain": list(plan.fallback_chain),
        "retry": {"attempts": plan.retry_attempts, "backoff": plan.retry_backoff},
    }


def fetch(args: argparse.Namespace) -> dict[str, object]:
    if not args.fixture:
        raise ScraperError("FetchError: fetch requires --fixture PATH (no network)")
    config = load_config(args.config)
    scraper = build_scraper(config, args).initialize()
    document = scraper.fetch(args.url)
    result: dict[str, object] = {
        "engine": scraper.engine_name,
        "processor": scraper.parser_name,
        "title": document.title,
        "status": "ok",
    }
    if args.report_attempts:
        result["attempts"] = scraper.last_retry.attempts
    if args.print_request_headers:
        result["request_headers"] = {
            key: REDACTED for key in scraper.request_headers
        }
    return result


def run(args: argparse.Namespace) -> dict[str, object]:
    config = load_config(args.config)
    resource_fields = parse_kv(args.job_resources)
    memory_str = resource_fields.get("memory", "0")
    resources = ResourceRequest.create(
        gpu=to_bool(resource_fields.get("gpu", "")), memory=memory_str
    )
    orchestrator = FakeOrchestrator(
        nodes=parse_nodes(args.node_capacity), store=FakeArtifactStore()
    )

    artifact_dir = Path(args.artifact_dir) if args.artifact_dir else None
    page_html = Path(args.fixture).read_text() if args.fixture else ""

    def produce(_index: int, node: str) -> str:
        if artifact_dir is not None:
            write_shard_summary(artifact_dir / node, config, args.url, page_html)
        return f"{node}/parsed_result.json"

    result = orchestrator.schedule(
        shards=args.shards, resources=resources, produce=produce
    )

    if args.artifact_store:
        publish_uploads(Path(args.artifact_store), result.uploaded)

    return {
        "shards": result.shards,
        "worker_nodes": list(result.worker_nodes),
        "artifacts": [shard.artifact for shard in result.shard_results],
        "uploaded": [Path(name).name for name in result.uploaded],
        "placement": {
            "gpu": resources.gpu,
            "memory": memory_str,
            "node": result.placement_node,
        },
    }
