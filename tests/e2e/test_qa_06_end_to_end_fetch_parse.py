"""Executable form of ``qa/06_end_to_end_fetch_parse.md``.

Covers scenario end_to_end_fetch_parse-1.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.e2e._cli import PAGE, TEST_URL, run_cli, write_config

COMBINATIONS = [
    ("requests", "beautifulsoup"),
    ("requests", "lxml"),
    ("selenium", "beautifulsoup"),
    ("playwright", "html.parser"),
]


@pytest.mark.parametrize(("engine", "processor"), COMBINATIONS)
def test_qa_6_1_full_pipeline_fetch_then_parse(
    engine: str, processor: str, tmp_path: Path
) -> None:
    config = write_config(
        tmp_path, f"scraper_engine: {engine}\nprocessing_type: {processor}\n"
    )

    result = run_cli(
        "fetch", "--config", config, "--fixture", str(PAGE), "--url", TEST_URL
    )

    assert result.code == 0
    plan = result.json
    assert plan["engine"] == engine
    assert plan["processor"] == processor
    assert plan["status"] == "ok"
    assert plan["title"] == "Test Page"
