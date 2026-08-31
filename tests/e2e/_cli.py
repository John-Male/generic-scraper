"""Drive the scraper's one user interface: ``python -m generic_scraper``.

The end-to-end QA suite (``tests/e2e/``) is the executable form of the prose
procedures in ``qa/``. It never imports :mod:`generic_scraper`; it launches the
CLI as a subprocess and asserts only on stdout, stderr, and exit code -- the
same surface a caller of the installed console script sees.

No network, no real browser, no real worker node: every command is given a
committed fixture with ``--fixture`` and the CLI always runs on the in-process
fake platform.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).parents[2]
CONFIGS = ROOT / "fixtures" / "configs"
PAGE = ROOT / "fixtures" / "test_page.html"
TEST_URL = "https://example.com/test-page"


@dataclass(frozen=True)
class CliResult:
    code: int
    stdout: str
    stderr: str

    @property
    def json(self) -> dict[str, object]:
        """Parsed stdout. Fails the test if stdout is not one JSON object."""

        assert self.stdout.strip(), (
            f"expected JSON on stdout, got nothing; stderr={self.stderr!r}"
        )
        parsed = json.loads(self.stdout)
        assert isinstance(parsed, dict)
        return parsed

    @property
    def combined(self) -> str:
        return self.stdout + self.stderr


def run_cli(*args: str) -> CliResult:
    """Invoke ``python -m generic_scraper <args>`` from the repo root."""

    completed = subprocess.run(
        [sys.executable, "-m", "generic_scraper", *args],
        cwd=ROOT,
        env={"PYTHONPATH": str(ROOT / "src"), "PATH": _path()},
        capture_output=True,
        text=True,
        timeout=30,
    )
    return CliResult(completed.returncode, completed.stdout, completed.stderr)


def write_config(tmp_path: Path, body: str) -> str:
    target = tmp_path / "config.yaml"
    target.write_text(body)
    return str(target)


def _path() -> str:
    import os

    return os.environ.get("PATH", "")
