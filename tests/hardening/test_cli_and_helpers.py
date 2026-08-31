"""Hardening for CLI parsing helpers and the command surface."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from generic_scraper.cli import main
from generic_scraper.cli.support import parse_kv, parse_memory_gb, parse_nodes

pytestmark = pytest.mark.hardening

ROOT = Path(__file__).parents[2]
CONFIGS = ROOT / "fixtures" / "configs"
PAGE = ROOT / "fixtures" / "test_page.html"

Cap = pytest.CaptureFixture[str]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2", 2.0),
        ("2gb", 2.0),
        ("2g", 2.0),
        ("512mb", 0.5),
        ("512m", 0.5),
    ],
)
def test_parse_memory_gb_unit_handling(text: str, expected: float) -> None:
    assert parse_memory_gb(text) == pytest.approx(expected)


def test_parse_memory_gb_rejects_junk_by_naming_it() -> None:
    with pytest.raises(ValueError) as excinfo:
        parse_memory_gb("a lot")

    assert str(excinfo.value) == "cannot read 'a lot' as a memory size"


@pytest.mark.parametrize("text", ["", None])
def test_parse_kv_of_nothing_is_empty(text: str | None) -> None:
    assert parse_kv(text) == {}


def test_parse_kv_keeps_pairs_after_an_empty_segment() -> None:
    assert parse_kv("gpu=true,,memory=2") == {"gpu": "true", "memory": "2"}


@pytest.mark.parametrize("spec", ["gpu=true,mem=4GB", "gpu=true,memory=4GB"])
def test_parse_nodes_applies_the_capacity_spec_to_every_node(spec: str) -> None:
    nodes = parse_nodes(spec)

    assert len(nodes) == 8
    assert all(node.gpu is True for node in nodes)
    assert all(node.memory_gb == pytest.approx(4.0) for node in nodes)


def test_parse_nodes_defaults_memory_to_8gb_when_only_gpu_is_given() -> None:
    nodes = parse_nodes("gpu=true")

    assert all(node.memory_gb == pytest.approx(8.0) for node in nodes)


def test_parse_nodes_without_a_spec_is_the_default_pool() -> None:
    nodes = parse_nodes("")

    assert len(nodes) == 8
    assert all(node.gpu is False for node in nodes)
    assert all(node.memory_gb == pytest.approx(8.0) for node in nodes)


def test_cli_requires_a_subcommand() -> None:
    with pytest.raises(SystemExit) as excinfo:
        main([])

    assert excinfo.value.code == 2


def test_cli_describe_output_keys_are_sorted(capsys: Cap) -> None:
    code = main(["describe", "--config", str(CONFIGS / "empty.yaml")])
    out = capsys.readouterr().out

    assert code == 0
    payload = json.loads(out)
    assert list(payload) == sorted(payload)


def test_cli_engine_start_failure_flag_forces_the_fallback(capsys: Cap) -> None:
    code = main(
        [
            "describe",
            "--config",
            str(CONFIGS / "selenium_secondary.yaml"),
            "--engine-start-failure",
            "selenium",
        ]
    )
    out = json.loads(capsys.readouterr().out)

    assert code == 0
    assert out["requested_engine"] == "selenium"
    assert out["engine"] == "requests"


def test_cli_run_creates_a_missing_artifact_store_tree(tmp_path: Path) -> None:
    store = tmp_path / "deep" / "nested" / "store"
    code = main(
        [
            "run",
            "--config",
            str(CONFIGS / "requests.yaml"),
            "--fixture",
            str(PAGE),
            "--artifact-store",
            str(store),
        ]
    )

    assert code == 0
    assert (store / "node-0" / "parsed_result.json").exists()


def test_cli_run_writes_a_parsed_artifact_per_shard(tmp_path: Path) -> None:
    artifacts = tmp_path / "artifacts"
    code = main(
        [
            "run",
            "--config",
            str(CONFIGS / "requests.yaml"),
            "--fixture",
            str(PAGE),
            "--shards",
            "2",
            "--artifact-dir",
            str(artifacts),
        ]
    )

    assert code == 0
    written = sorted(artifacts.glob("*/parsed_result.json"))
    assert len(written) == 2
    for path in written:
        assert json.loads(path.read_text())["title"] == "Test Page"
