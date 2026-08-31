"""Command-line interface: ``describe``, ``fetch``, and ``run``.

This is the only user interface. Every command reads a YAML ``ScraperType`` with
``--config``, prints exactly one JSON object to stdout on success and exits 0,
and on a handled error prints nothing to stdout, writes a message beginning with
the error class name to stderr, and exits non-zero.

No command touches a network or a real browser. The engine platform is always
the in-process fake; QA affordance flags configure it.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from generic_scraper.config import ScraperType
from generic_scraper.engines.fake_platform import FakePlatform
from generic_scraper.errors import ScraperError
from generic_scraper.orchestrator import (
    FakeArtifactStore,
    FakeOrchestrator,
    NodeCapacity,
    ResourceRequest,
    homogeneous_nodes,
    parse_memory_gb,
)
from generic_scraper.scraper import Scraper

REDACTED = "***"


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        result = args.handler(args)
    except ScraperError as error:
        print(str(error), file=sys.stderr)
        return 1
    except (OSError, ValueError) as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        return 1
    json.dump(result, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


# -- commands -----------------------------------------------------------


def _describe(args: argparse.Namespace) -> dict[str, object]:
    config = _load_config(args.config)
    scraper = _new_scraper(config, args).initialize()
    plan = scraper.plan()
    header = plan.proxy_header
    return {
        "engine": plan.engine,
        "requested_engine": plan.requested_engine,
        "browser": plan.browser,
        "processor": plan.processor,
        "proxy": plan.proxy,
        "proxy_header": _redact_header(header),
        "fallback_chain": list(plan.fallback_chain),
        "retry": {"attempts": plan.retry_attempts, "backoff": plan.retry_backoff},
    }


def _fetch(args: argparse.Namespace) -> dict[str, object]:
    if not args.fixture:
        raise ScraperError("FetchError: fetch requires --fixture PATH (no network)")
    config = _load_config(args.config)
    scraper = _new_scraper(config, args).initialize()
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


def _run(args: argparse.Namespace) -> dict[str, object]:
    config = _load_config(args.config)
    resource_fields = _parse_kv(args.job_resources)
    memory_str = resource_fields.get("memory", "0")
    resources = ResourceRequest.create(
        gpu=_as_bool(resource_fields.get("gpu", "")), memory=memory_str
    )
    nodes = _parse_nodes(args.node_capacity)
    store = FakeArtifactStore()
    orchestrator = FakeOrchestrator(nodes=nodes, store=store)

    artifact_dir = Path(args.artifact_dir) if args.artifact_dir else None
    page_html = Path(args.fixture).read_text() if args.fixture else ""

    def produce(_index: int, node: str) -> str:
        if artifact_dir is not None:
            _write_shard_summary(artifact_dir / node, config, args.url, page_html)
        return f"{node}/parsed_result.json"

    result = orchestrator.schedule(
        shards=args.shards, resources=resources, produce=produce
    )

    if args.artifact_store:
        _publish_uploads(Path(args.artifact_store), result.uploaded)

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


# -- helpers ----------------------------------------------------------


def _new_scraper(config: ScraperType, args: argparse.Namespace) -> Scraper:
    page_html = Path(args.fixture).read_text() if getattr(args, "fixture", None) else ""
    platform = FakePlatform.build(
        page_html=page_html,
        unavailable=list(getattr(args, "engine_unavailable", []) or []),
        start_failures=list(getattr(args, "engine_start_failure", []) or []),
        transient_errors=int(getattr(args, "transient_errors", 0) or 0),
    )
    return Scraper(config, platform)


def _shard_summary(config: ScraperType, url: str, page_html: str) -> dict[str, object]:
    scraper = Scraper(config, FakePlatform.build(page_html=page_html)).initialize()
    document = scraper.fetch(url)
    return {
        "engine": scraper.engine_name,
        "processor": scraper.parser_name,
        "title": document.title,
    }


def _write_shard_summary(
    node_dir: Path, config: ScraperType, url: str, page_html: str
) -> None:
    target = node_dir / "parsed_result.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    summary = _shard_summary(config, url, page_html)
    target.write_text(json.dumps(summary, sort_keys=True))


def _publish_uploads(store_dir: Path, names: Sequence[str]) -> None:
    store_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        (store_dir / Path(name).name).write_text("uploaded\n")


def _load_config(path: str | None) -> ScraperType:
    if not path:
        return ScraperType.from_dict({})
    return ScraperType.from_yaml(path)


def _redact_header(header: str | None) -> str | None:
    if header is None:
        return None
    key, _, _value = header.partition(":")
    return f"{key.strip()}: {REDACTED}"


def _parse_kv(text: str | None) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for chunk in (text or "").split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        key, _, value = chunk.partition("=")
        pairs[key.strip().lower()] = value.strip()
    return pairs


def _as_bool(text: str, *, default: bool = False) -> bool:
    if not text:
        return default
    return text.strip().lower() in {"true", "yes", "1", "on"}


def _parse_nodes(text: str | None) -> tuple[NodeCapacity, ...]:
    if not text:
        return homogeneous_nodes()
    fields = _parse_kv(text)
    return homogeneous_nodes(
        gpu=_as_bool(fields.get("gpu", "")),
        memory_gb=parse_memory_gb(fields.get("mem", fields.get("memory", "8GB"))),
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="generic-scraper")
    subs = parser.add_subparsers(dest="command", required=True)

    def add_common(sub: argparse.ArgumentParser) -> None:
        sub.add_argument("--config", help="path to a YAML ScraperType file")

    describe = subs.add_parser("describe", help="print the resolved scraper plan")
    add_common(describe)
    _add_engine_flags(describe)
    describe.set_defaults(handler=_describe, fixture=None)

    fetch = subs.add_parser("fetch", help="fetch one URL and parse it")
    add_common(fetch)
    _add_engine_flags(fetch)
    fetch.add_argument("--url", default="https://example.com/test-page")
    fetch.add_argument("--fixture", help="read this saved page instead of the network")
    fetch.add_argument("--report-attempts", action="store_true")
    fetch.add_argument("--print-request-headers", action="store_true")
    fetch.set_defaults(handler=_fetch)

    run = subs.add_parser("run", help="schedule a sharded job on the fake orchestrator")
    add_common(run)
    run.add_argument("--url", default="https://example.com/test-page")
    run.add_argument("--fixture")
    run.add_argument("--shards", type=int, default=1)
    run.add_argument("--artifact-dir")
    run.add_argument("--artifact-store")
    run.add_argument("--orchestrator", choices=["fake"], default="fake")
    run.add_argument("--job-resources", default="")
    run.add_argument("--node-capacity", default="")
    run.set_defaults(handler=_run)

    return parser


def _add_engine_flags(sub: argparse.ArgumentParser) -> None:
    sub.add_argument("--engine-unavailable", action="append", default=[])
    sub.add_argument("--engine-start-failure", action="append", default=[])
    sub.add_argument("--transient-errors", type=int, default=0)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
