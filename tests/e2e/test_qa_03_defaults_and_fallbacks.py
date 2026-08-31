"""Executable form of ``qa/03_defaults_and_fallbacks.md``.

Covers scenarios defaults_and_fallbacks-1 and defaults_and_fallbacks-2.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.e2e._cli import CONFIGS, run_cli, write_config


def test_qa_3_1_empty_config_uses_documented_defaults() -> None:
    result = run_cli("describe", "--config", str(CONFIGS / "empty.yaml"))

    assert result.code == 0
    plan = result.json
    assert plan["engine"] == "requests"
    assert plan["browser"] is None


@pytest.mark.parametrize("engine", ["playwright", "selenium"])
def test_qa_3_2_unavailable_primary_falls_back_to_requests(
    engine: str, tmp_path: Path
) -> None:
    config = write_config(tmp_path, f"scraper_engine: {engine}\n")

    result = run_cli(
        "describe", "--config", config, "--engine-unavailable", engine
    )

    assert result.code == 0
    plan = result.json
    assert plan["requested_engine"] == engine
    assert plan["engine"] == "requests"
    assert plan["fallback_chain"] == [engine, "requests"]
