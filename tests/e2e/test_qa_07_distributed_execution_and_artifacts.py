"""Executable form of ``qa/07_distributed_execution_and_artifacts.md``.

Covers scenarios distributed_execution_and_artifacts-1..3. Every run uses the
default fake orchestrator; no real worker node is contacted.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.e2e._cli import CONFIGS, PAGE, TEST_URL, run_cli, write_config


@pytest.mark.parametrize("shards", [3, 5])
def test_qa_7_1_job_runs_across_distinct_workers_each_with_an_artifact(
    shards: int, tmp_path: Path
) -> None:
    artifact_dir = tmp_path / "artifacts"

    result = run_cli(
        "run",
        "--config",
        str(CONFIGS / "requests.yaml"),
        "--url",
        TEST_URL,
        "--fixture",
        str(PAGE),
        "--shards",
        str(shards),
        "--artifact-dir",
        str(artifact_dir),
    )

    assert result.code == 0
    plan = result.json
    assert plan["shards"] == shards
    assert len(plan["worker_nodes"]) == shards
    assert len(set(plan["worker_nodes"])) == shards
    assert len(plan["artifacts"]) == shards
    for name in plan["artifacts"]:
        assert (artifact_dir / name).is_file()


def test_qa_7_2_each_finished_shard_uploads_its_artifact_to_the_store(
    tmp_path: Path,
) -> None:
    artifact_dir = tmp_path / "artifacts"
    store = tmp_path / "store"

    result = run_cli(
        "run",
        "--config",
        str(CONFIGS / "requests.yaml"),
        "--url",
        TEST_URL,
        "--fixture",
        str(PAGE),
        "--shards",
        "3",
        "--artifact-dir",
        str(artifact_dir),
        "--artifact-store",
        str(store),
    )

    assert result.code == 0
    plan = result.json
    assert plan["uploaded"] == ["parsed_result.json"] * 3
    uploaded_files = sorted(
        p.relative_to(store).as_posix() for p in store.rglob("*.json")
    )
    assert uploaded_files == [
        f"{node}/parsed_result.json" for node in plan["worker_nodes"]
    ]


def test_qa_7_3_job_is_placed_on_a_node_satisfying_resource_constraints(
    tmp_path: Path,
) -> None:
    config = write_config(tmp_path, "browser_type: chrome\n")
    base = [
        "run",
        "--config",
        config,
        "--url",
        TEST_URL,
        "--fixture",
        str(PAGE),
        "--shards",
        "1",
        "--artifact-dir",
        str(tmp_path / "artifacts"),
        "--job-resources",
        "gpu=false,memory=2GB",
    ]

    ok = run_cli(*base, "--node-capacity", "gpu=false,mem=4GB")
    assert ok.code == 0
    placement = ok.json["placement"]
    assert placement["gpu"] is False
    assert placement["memory"] == "2GB"
    assert placement["node"].startswith("node-")

    too_small = run_cli(*base, "--node-capacity", "gpu=false,mem=1GB")
    assert too_small.code != 0
    assert too_small.stdout == ""
    # A descriptive placement error that names the unsatisfied constraint.
    assert too_small.stderr.startswith("ScraperError")
    assert "constraint" in too_small.stderr
    assert "memory>=2GB" in too_small.stderr
