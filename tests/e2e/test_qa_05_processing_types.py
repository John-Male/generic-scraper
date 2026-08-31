"""Executable form of ``qa/05_processing_types.md`` (scenario processing_types-1)."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.e2e._cli import PAGE, TEST_URL, run_cli, write_config

PROCESSORS = ["beautifulsoup", "lxml", "html.parser", "regex"]


@pytest.mark.parametrize("processor", PROCESSORS)
def test_qa_5_1_processing_type_is_selected(processor: str, tmp_path: Path) -> None:
    config = write_config(tmp_path, f"processing_type: {processor}\n")

    result = run_cli("describe", "--config", config)

    assert result.code == 0
    assert result.json["processor"] == processor


@pytest.mark.parametrize("processor", PROCESSORS)
def test_qa_5_2_processing_type_parses_a_page(processor: str, tmp_path: Path) -> None:
    config = write_config(tmp_path, f"processing_type: {processor}\n")

    result = run_cli(
        "fetch", "--config", config, "--fixture", str(PAGE), "--url", TEST_URL
    )

    assert result.code == 0
    plan = result.json
    assert plan["processor"] == processor
    assert plan["status"] == "ok"
    assert plan["title"] == "Test Page"
