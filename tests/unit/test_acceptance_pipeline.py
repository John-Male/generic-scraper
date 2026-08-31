"""Unit tests for the acceptance runtime, registry, and entrypoint generator."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tests.acceptance import registry
from tests.acceptance import runtime as runtime_mod
from tests.acceptance.registry import StepError, match, step
from tests.acceptance.runtime import World, iter_executions, run_execution

ROOT = Path(__file__).parents[2]
GENERATOR = ROOT / "scripts" / "acceptance-entrypoint-generator"

SAMPLE_IR = {
    "name": "Sample",
    "background": [{"keyword": "Given", "text": "a start"}],
    "scenarios": [
        {
            "name": "sample-1",
            "steps": [
                {"keyword": "When", "text": 'the value is "<value>"'},
                {"keyword": "Then", "text": "it is recorded"},
            ],
            "examples": [{"value": "a"}, {"value": "b"}],
        }
    ],
}


@pytest.fixture(autouse=True)
def _isolate_registry() -> object:
    saved = list(registry._HANDLERS)
    saved_loaded = runtime_mod._STEPS_LOADED
    registry._HANDLERS.clear()
    runtime_mod._STEPS_LOADED = True  # keep run_execution from loading real handlers
    yield
    registry._HANDLERS[:] = saved
    runtime_mod._STEPS_LOADED = saved_loaded


def test_iter_executions_expands_one_execution_per_example_row() -> None:
    executions = iter_executions(SAMPLE_IR)

    assert [e.id for e in executions] == ["sample-1/example_1", "sample-1/example_2"]
    assert executions[0].steps[0] == ("Given", "a start")
    assert executions[0].example == {"value": "a"}


def test_scenario_without_examples_runs_once() -> None:
    ir = {"name": "S", "scenarios": [{"name": "s-1", "steps": []}]}

    executions = iter_executions(ir)

    assert len(executions) == 1
    assert executions[0].example == {}


def test_registry_reports_unsupported_step() -> None:
    with pytest.raises(StepError, match="unsupported step"):
        match("nothing matches this")


def test_registry_reports_ambiguous_step() -> None:
    step(r"the value is .+")(lambda world: None)
    step(r"the value is \"x\"")(lambda world: None)

    with pytest.raises(StepError, match="ambiguous"):
        match('the value is "x"')


def test_run_execution_resolves_placeholders_and_dispatches() -> None:
    seen: list[str] = []
    step(r"a start")(lambda world: seen.append("start"))
    step(r'the value is "(?P<value>[^"]+)"')(
        lambda world, value: seen.append(f"value={value}")
    )
    step(r"it is recorded")(lambda world: seen.append("recorded"))

    run_execution(iter_executions(SAMPLE_IR)[1])

    assert seen == ["start", "value=b", "recorded"]


def test_run_execution_fails_on_missing_example_value() -> None:
    step(r"a start")(lambda world: None)
    step(r'the value is "(?P<value>[^"]+)"')(lambda world, value: None)
    step(r"it is recorded")(lambda world: None)
    broken = iter_executions(
        {
            "name": "S",
            "scenarios": [
                {
                    "name": "s-1",
                    "steps": [{"keyword": "When", "text": 'the value is "<value>"'}],
                    "examples": [{}],
                }
            ],
        }
    )[0]

    with pytest.raises(StepError, match="missing example value"):
        run_execution(broken)


def test_world_is_fresh_per_execution() -> None:
    captured: list[int] = []

    def record(world: World) -> None:
        world.shards += 1
        captured.append(world.shards)

    step(r"a start")(record)
    step(r'the value is "(?P<value>[^"]+)"')(lambda world, value: None)
    step(r"it is recorded")(lambda world: None)

    for execution in iter_executions(SAMPLE_IR):
        run_execution(execution)

    assert captured == [2, 2]


def test_generator_writes_deterministic_module_and_metadata(tmp_path: Path) -> None:
    ir_path = tmp_path / "sample.json"
    ir_path.write_text(json.dumps(SAMPLE_IR))
    out_dir = tmp_path / "generated"

    first = subprocess.run(
        [sys.executable, str(GENERATOR), str(ir_path), str(out_dir)],
        capture_output=True,
        text=True,
    )
    module = (out_dir / "test_sample.py").read_text()
    second = subprocess.run(
        [sys.executable, str(GENERATOR), str(ir_path), str(out_dir)],
        capture_output=True,
        text=True,
    )

    assert first.returncode == 0
    assert second.returncode == 0
    assert (out_dir / "test_sample.py").read_text() == module
    assert "iter_executions" in module

    meta = json.loads(
        (out_dir / "metadata" / "features-sample-feature.json").read_text()
    )
    assert meta["schema_version"] == 1
    assert meta["hash_scope"] == "generated_files"
    assert meta["implementation_hash"].startswith("sha256:")


def test_generator_rejects_wrong_arg_count(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(GENERATOR), str(tmp_path / "only-one.json")],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
