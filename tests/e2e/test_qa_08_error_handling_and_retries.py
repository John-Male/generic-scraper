"""Executable form of ``qa/08_error_handling_and_retries.md``.

Covers scenarios error_handling_and_retries-1..3.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from tests.e2e._cli import CONFIGS, PAGE, TEST_URL, run_cli, write_config

RETRY_CONFIGS = [
    (CONFIGS / "retry.yaml", 3),
    (CONFIGS / "retry_5.yaml", 5),
]


@pytest.mark.parametrize(("config", "attempts"), RETRY_CONFIGS)
def test_qa_8_1_transient_errors_are_retried_up_to_the_attempt_count(
    config: Path, attempts: int
) -> None:
    base = [
        "fetch",
        "--config",
        str(config),
        "--url",
        TEST_URL,
        "--fixture",
        str(PAGE),
        "--report-attempts",
    ]

    started = time.monotonic()
    exhausted = run_cli(*base, "--transient-errors", str(attempts + 1))
    elapsed = time.monotonic() - started

    assert exhausted.code != 0
    assert exhausted.stdout == ""
    assert "TransientFetchError" in exhausted.stderr
    assert f"{attempts} attempt(s)" in exhausted.stderr
    # Backoff runs on an injected clock: no real wall-clock delay.
    assert elapsed < 10

    recovered = run_cli(*base, "--transient-errors", str(attempts - 1))
    assert recovered.code == 0
    plan = recovered.json
    assert plan["status"] == "ok"
    assert plan["attempts"] == attempts


@pytest.mark.parametrize("engine", ["selenium", "playwright"])
def test_qa_8_2_engine_start_failure_falls_back_to_secondary(
    engine: str, tmp_path: Path
) -> None:
    config = write_config(
        tmp_path, f"scraper_engine: {engine}\nsecondary: requests\n"
    )

    result = run_cli(
        "describe", "--config", config, "--engine-start-failure", engine
    )

    assert result.code == 0
    plan = result.json
    assert plan["engine"] == "requests"
    assert plan["fallback_chain"] == [engine, "requests"]
    assert plan["requested_engine"] == engine


def test_qa_8_3_unknown_engine_fails_with_a_descriptive_named_error() -> None:
    result = run_cli(
        "describe", "--config", str(CONFIGS / "unknown_engine.yaml")
    )

    assert result.code != 0
    assert result.stdout == ""
    assert result.stderr.split(":", 1)[0] == "UnsupportedScraperEngineError"
    assert "unknown" in result.stderr
