"""Executable form of ``qa/01_initialize_scraper.md``.

Covers scenario initialize_scraper-1.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.e2e._cli import PAGE, TEST_URL, run_cli, write_config

ENGINES = ["requests", "playwright", "selenium"]


@pytest.mark.parametrize("engine", ENGINES)
def test_qa_1_1_engine_is_selected_and_ready(engine: str, tmp_path: Path) -> None:
    config = write_config(tmp_path, f"scraper_engine: {engine}\n")

    described = run_cli("describe", "--config", config)
    assert described.code == 0
    plan = described.json
    assert plan["engine"] == engine
    assert plan["requested_engine"] == engine
    assert plan["fallback_chain"] == [engine]

    fetched = run_cli(
        "fetch", "--config", config, "--fixture", str(PAGE), "--url", TEST_URL
    )
    assert fetched.code == 0
    assert fetched.json["status"] == "ok"


def test_qa_1_2_unknown_engine_is_rejected(tmp_path: Path) -> None:
    config = write_config(tmp_path, "scraper_engine: bogus\n")

    result = run_cli("describe", "--config", config)

    assert result.code != 0
    assert result.stdout == ""
    assert result.stderr.startswith("UnsupportedScraperEngineError")
