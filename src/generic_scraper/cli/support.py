"""Helpers shared by the CLI command handlers.

Config loading, fake-platform assembly, ``key=value`` parsing, and the small
amount of artifact file output the ``run`` command performs. No argparse here.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from generic_scraper.config import ScraperType
from generic_scraper.engines.fake_platform import FakePlatform
from generic_scraper.orchestrator import (
    NodeCapacity,
    homogeneous_nodes,
    parse_memory_gb,
)
from generic_scraper.scraper import Scraper

REDACTED = "***"
_TRUTHY = {"true", "yes", "1", "on"}


def build_scraper(config: ScraperType, args: argparse.Namespace) -> Scraper:
    """A scraper on a fake platform configured by the QA affordance flags."""

    page_html = (
        Path(args.fixture).read_text() if getattr(args, "fixture", None) else ""
    )
    platform = FakePlatform.build(
        page_html=page_html,
        unavailable=list(getattr(args, "engine_unavailable", []) or []),
        start_failures=list(getattr(args, "engine_start_failure", []) or []),
        transient_errors=int(getattr(args, "transient_errors", 0) or 0),
    )
    return Scraper(config, platform)


def shard_summary(config: ScraperType, url: str, page_html: str) -> dict[str, object]:
    scraper = Scraper(config, FakePlatform.build(page_html=page_html)).initialize()
    document = scraper.fetch(url)
    return {
        "engine": scraper.engine_name,
        "processor": scraper.parser_name,
        "title": document.title,
    }


def write_shard_summary(
    node_dir: Path, config: ScraperType, url: str, page_html: str
) -> None:
    target = node_dir / "parsed_result.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(shard_summary(config, url, page_html), sort_keys=True))


def publish_uploads(store_dir: Path, names: Sequence[str]) -> None:
    store_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        (store_dir / Path(name).name).write_text("uploaded\n")


def load_config(path: str | None) -> ScraperType:
    if not path:
        return ScraperType.from_dict({})
    return ScraperType.from_yaml(path)


def redact_header(header: str | None) -> str | None:
    if header is None:
        return None
    key, _, _value = header.partition(":")
    return f"{key.strip()}: {REDACTED}"


def parse_kv(text: str | None) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for chunk in (text or "").split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        key, _, value = chunk.partition("=")
        pairs[key.strip().lower()] = value.strip()
    return pairs


def to_bool(text: str, *, default: bool = False) -> bool:
    if not text:
        return default
    return text.strip().lower() in _TRUTHY


def parse_nodes(text: str | None) -> tuple[NodeCapacity, ...]:
    if not text:
        return homogeneous_nodes()
    fields = parse_kv(text)
    return homogeneous_nodes(
        gpu=to_bool(fields.get("gpu", "")),
        memory_gb=parse_memory_gb(fields.get("mem", fields.get("memory", "8GB"))),
    )
