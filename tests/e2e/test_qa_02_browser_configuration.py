"""Executable form of ``qa/02_browser_configuration.md``.

Covers scenario browser_configuration-1.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from tests.e2e._cli import run_cli, write_config

PAIRS = [
    ("playwright", "chrome"),
    ("playwright", "firefox"),
    ("selenium", "chrome"),
    ("selenium", "firefox"),
]


@pytest.mark.parametrize(("engine", "browser"), PAIRS)
def test_qa_2_1_browser_type_is_honored(
    engine: str, browser: str, tmp_path: Path
) -> None:
    config = write_config(
        tmp_path, f"scraper_engine: {engine}\nbrowser_type: {browser}\n"
    )

    started = time.monotonic()
    result = run_cli("describe", "--config", config)
    elapsed = time.monotonic() - started

    assert result.code == 0
    plan = result.json
    assert plan["engine"] == engine
    assert plan["browser"] == browser
    # No real browser process is launched: the fake driver just records the
    # requested pair, so describe returns effectively instantly and never
    # falls back.
    assert plan["fallback_chain"] == [engine]
    assert elapsed < 10
