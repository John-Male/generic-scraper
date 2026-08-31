"""Lightweight automated architecture checks.

These guard the boundaries the module layout is meant to enforce: no import
cycles, high-level policy never importing an IO-near adapter, and heavy IO
libraries staying out of module-level imports.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[2] / "src"
_PKG = "generic_scraper"


def _modules() -> dict[str, ast.Module]:
    trees: dict[str, ast.Module] = {}
    for path in sorted(_SRC.rglob("*.py")):
        rel = path.relative_to(_SRC).with_suffix("")
        name = ".".join(rel.parts)
        if name.endswith(".__init__"):
            name = name[: -len(".__init__")]
        trees[name] = ast.parse(path.read_text(), str(path))
    return trees


def _internal_imports(name: str, tree: ast.Module) -> set[str]:
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.startswith(_PKG):
                out.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(_PKG):
                    out.add(alias.name)
    return out


def _module_level_imports(tree: ast.Module) -> set[str]:
    out: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            out.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            out.add(node.module.split(".")[0])
    return out


def test_no_import_cycles_within_the_package() -> None:
    graph = {name: _internal_imports(name, tree) for name, tree in _modules().items()}

    def walk(node: str, seen: tuple[str, ...]) -> list[str] | None:
        if node in seen:
            return [*seen[seen.index(node) :], node]
        for nxt in sorted(graph.get(node, ())):
            cycle = walk(nxt, (*seen, node))
            if cycle:
                return cycle
        return None

    for start in graph:
        cycle = walk(start, ())
        assert cycle is None, f"import cycle: {' -> '.join(cycle)}"


def test_scraper_policy_depends_only_on_interfaces() -> None:
    allowed = {
        f"{_PKG}.config",
        f"{_PKG}.errors",
        f"{_PKG}.retry",
        f"{_PKG}.retry_policy",
        f"{_PKG}.engines.base",
        f"{_PKG}.engines.platform",
        f"{_PKG}.parsers.base",
        f"{_PKG}.parsers.registry",
    }
    scraper = f"{_PKG}.scraper"
    imports = _internal_imports(scraper, _modules()[scraper])
    leaked = imports - allowed
    assert not leaked, f"scraper.py reaches past its interfaces: {sorted(leaked)}"


@pytest.mark.parametrize(
    "module",
    [
        "scraper",
        "config",
        "retry",
        "retry_policy",
        "orchestrator",
        "errors",
        "engines.base",
        "engines.platform",
        "parsers.base",
        "parsers.registry",
    ],
)
def test_high_level_modules_do_not_import_io_libraries(module: str) -> None:
    forbidden = {"requests", "bs4", "lxml", "playwright", "selenium", "argparse"}
    if module != "config":
        forbidden.add("yaml")
    at_module_level = _module_level_imports(_modules()[f"{_PKG}.{module}"])
    assert not (at_module_level & forbidden), (
        f"{module} imports {sorted(at_module_level & forbidden)} at module level"
    )
