"""The gherkin-mutator worker adapter, driven directly over its stdin/stdout."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.hardening

ROOT = Path(__file__).parents[2]
RUNNER = ROOT / "scripts" / "acceptance-mutation-runner"
BASE_IR = ROOT / "tests" / "acceptance" / "ir" / "01_initialize_scraper.json"


def _run_jobs(*jobs: dict) -> list[dict]:
    stdin = "\n".join(json.dumps(job) for job in jobs) + "\n"
    proc = subprocess.run(
        [sys.executable, str(RUNNER)],
        input=stdin,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert proc.returncode == 0, proc.stderr
    return [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]


def test_unmutated_ir_reports_test_success() -> None:
    (result,) = _run_jobs({"id": "m0", "feature_json": str(BASE_IR)})

    assert result["id"] == "m0"
    assert result["outcome"] == "test_success"
    assert result["error"] == ""


def test_a_spec_change_the_scenario_catches_reports_test_failure(
    tmp_path: Path,
) -> None:
    ir = json.loads(BASE_IR.read_text())
    ir["scenarios"][0]["examples"][0]["engine"] = "reqXuests"
    mutated = tmp_path / "feature.json"
    mutated.write_text(json.dumps(ir))

    (result,) = _run_jobs({"id": "m1", "feature_json": str(mutated)})

    assert result["outcome"] == "test_failure"
    assert result["error"]


def test_an_unreadable_ir_is_an_infrastructure_error() -> None:
    (result,) = _run_jobs({"id": "m2", "feature_json": "/no/such/feature.json"})

    assert result["outcome"] == "infrastructure_error"


def test_the_worker_stays_hot_across_several_jobs(tmp_path: Path) -> None:
    ir = json.loads(BASE_IR.read_text())
    ir["scenarios"][0]["examples"][0]["engine"] = "reqXuests"
    mutated = tmp_path / "feature.json"
    mutated.write_text(json.dumps(ir))

    results = _run_jobs(
        {"id": "a", "feature_json": str(BASE_IR)},
        {"id": "b", "feature_json": str(mutated)},
        {"id": "c", "feature_json": str(BASE_IR)},
    )

    assert [r["id"] for r in results] == ["a", "b", "c"]
    assert [r["outcome"] for r in results] == [
        "test_success",
        "test_failure",
        "test_success",
    ]
