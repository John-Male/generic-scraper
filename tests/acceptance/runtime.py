"""Acceptance runtime: expand JSON IR into executions and run their steps.

The generated entry points call :func:`iter_executions` to parametrise and
:func:`run_execution` to execute. This module never parses a ``.feature`` file;
it works only from parser-produced JSON IR.
"""

from __future__ import annotations

import importlib
import pkgutil
import re
from dataclasses import dataclass, field
from typing import Any

from tests.acceptance import steps as _steps_pkg
from tests.acceptance.registry import StepError, match

_PLACEHOLDER = re.compile(r"<([A-Za-z0-9_]+)>")
_STEPS_LOADED = False


def _load_steps() -> None:
    global _STEPS_LOADED
    if _STEPS_LOADED:
        return
    for module in pkgutil.iter_modules(_steps_pkg.__path__):
        importlib.import_module(f"{_steps_pkg.__name__}.{module.name}")
    _STEPS_LOADED = True


@dataclass
class World:
    """Fresh per execution. Shared by that execution's steps."""

    config: dict[str, Any] = field(default_factory=dict)
    unavailable: set[str] = field(default_factory=set)
    start_failures: set[str] = field(default_factory=set)
    transient_errors: int = 0
    url: str = "https://example.com/test-page"
    shards: int = 1
    resources: Any = None
    artifact: str | None = None
    scraper: Any = None
    platform: Any = None
    document: Any = None
    job: Any = None
    store: Any = None
    error: BaseException | None = None
    retry_attempts: int = 0
    initialized: bool = False
    parsed_titles: list[str | None] = field(default_factory=list)


@dataclass(frozen=True)
class Execution:
    feature: str
    scenario: str
    index: int
    steps: tuple[tuple[str, str], ...]
    example: dict[str, str]

    @property
    def id(self) -> str:
        return f"{self.scenario}/example_{self.index}"


def iter_executions(ir: dict[str, Any]) -> list[Execution]:
    background = tuple(
        (s["keyword"], s["text"]) for s in ir.get("background", []) or []
    )
    executions: list[Execution] = []
    for scenario in ir["scenarios"]:
        steps = tuple((s["keyword"], s["text"]) for s in scenario["steps"])
        rows = scenario.get("examples") or [{}]
        for index, row in enumerate(rows, start=1):
            executions.append(
                Execution(
                    feature=ir["name"],
                    scenario=scenario["name"],
                    index=index,
                    steps=background + steps,
                    example={k: str(v) for k, v in row.items()},
                )
            )
    return executions


def _resolve(text: str, example: dict[str, str]) -> str:
    def substitute(hit: re.Match[str]) -> str:
        key = hit.group(1)
        if key not in example:
            raise StepError(f"missing example value for <{key}> in step {text!r}")
        return example[key]

    return _PLACEHOLDER.sub(substitute, text)


def run_execution(execution: Execution) -> None:
    _load_steps()
    world = World()
    for _keyword, raw_text in execution.steps:
        resolved = _resolve(raw_text, execution.example)
        handler, captures = match(resolved)
        handler(world, **captures)
