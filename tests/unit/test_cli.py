"""Unit tests for the command-line interface."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from generic_scraper.cli import main

ROOT = Path(__file__).parents[2]
CONFIGS = ROOT / "fixtures" / "configs"
PAGE = ROOT / "fixtures" / "test_page.html"

Cap = pytest.CaptureFixture[str]


def _run(capsys: Cap, *argv: str) -> tuple[int, dict, str]:
    code = main(list(argv))
    captured = capsys.readouterr()
    payload = json.loads(captured.out) if captured.out.strip() else {}
    return code, payload, captured.err


def test_describe_reports_defaults_for_empty_config(capsys: Cap) -> None:
    code, out, _ = _run(capsys, "describe", "--config", str(CONFIGS / "empty.yaml"))

    assert code == 0
    assert out["engine"] == "requests"
    assert out["browser"] is None
    assert out["retry"] == {"attempts": 1, "backoff": "exponential"}


def test_describe_shows_fallback_chain_when_engine_unavailable(
    capsys: Cap,
) -> None:
    code, out, _ = _run(
        capsys,
        "describe",
        "--config",
        str(CONFIGS / "playwright_chrome.yaml"),
        "--engine-unavailable",
        "playwright",
    )

    assert code == 0
    assert out["engine"] == "requests"
    assert out["requested_engine"] == "playwright"
    assert out["fallback_chain"] == ["playwright", "requests"]


def test_describe_redacts_the_proxy_pass_value(capsys: Cap) -> None:
    code, out, _ = _run(
        capsys, "describe", "--config", str(CONFIGS / "proxy_header.yaml")
    )

    assert code == 0
    assert out["proxy_header"] == "X-Proxy-Auth: ***"


def test_describe_unknown_engine_exits_nonzero_with_class_name(
    capsys: Cap,
) -> None:
    code, out, err = _run(
        capsys, "describe", "--config", str(CONFIGS / "unknown_engine.yaml")
    )

    assert code == 1
    assert out == {}
    assert err.startswith("UnsupportedScraperEngineError")


def test_fetch_returns_document_summary(capsys: Cap) -> None:
    code, out, _ = _run(
        capsys,
        "fetch",
        "--config",
        str(CONFIGS / "requests.yaml"),
        "--fixture",
        str(PAGE),
    )

    assert code == 0
    assert out == {
        "engine": "requests",
        "processor": "beautifulsoup",
        "title": "Test Page",
        "status": "ok",
    }


def test_fetch_reports_attempts_and_redacted_headers(
    capsys: Cap,
) -> None:
    code, out, _ = _run(
        capsys,
        "fetch",
        "--config",
        str(CONFIGS / "proxy_header.yaml"),
        "--fixture",
        str(PAGE),
        "--report-attempts",
        "--print-request-headers",
    )

    assert code == 0
    assert out["attempts"] == 1
    assert out["request_headers"] == {"X-Proxy-Auth": "***"}


def test_fetch_retries_then_fails_on_persistent_transient_errors(
    capsys: Cap,
) -> None:
    code, out, err = _run(
        capsys,
        "fetch",
        "--config",
        str(CONFIGS / "requests.yaml"),
        "--fixture",
        str(PAGE),
        "--transient-errors",
        "9",
    )

    assert code == 1
    assert out == {}
    assert err.startswith("FetchError")


def test_run_shards_job_and_uploads_artifacts(
    capsys: Cap, tmp_path: Path
) -> None:
    code, out, _ = _run(
        capsys,
        "run",
        "--config",
        str(CONFIGS / "requests.yaml"),
        "--fixture",
        str(PAGE),
        "--shards",
        "3",
        "--artifact-dir",
        str(tmp_path / "artifacts"),
        "--artifact-store",
        str(tmp_path / "store"),
    )

    assert code == 0
    assert out["shards"] == 3
    assert len(set(out["worker_nodes"])) == 3
    assert out["uploaded"] == ["parsed_result.json"] * 3
    assert (tmp_path / "store" / "parsed_result.json").exists()


def test_run_places_job_on_a_node_that_meets_resource_limits(
    capsys: Cap,
) -> None:
    code, out, _ = _run(
        capsys,
        "run",
        "--config",
        str(CONFIGS / "playwright_chrome.yaml"),
        "--fixture",
        str(PAGE),
        "--job-resources",
        "gpu=false,memory=2GB",
    )

    assert code == 0
    assert out["placement"]["gpu"] is False
    assert out["placement"]["memory"] == "2GB"
    assert out["placement"]["node"].startswith("node-")


def test_run_fails_when_no_node_satisfies_constraints(
    capsys: Cap,
) -> None:
    code, _out, err = _run(
        capsys,
        "run",
        "--config",
        str(CONFIGS / "requests.yaml"),
        "--fixture",
        str(PAGE),
        "--job-resources",
        "gpu=true,memory=2GB",
        "--node-capacity",
        "gpu=false,mem=8GB",
    )

    assert code == 1
    assert err.startswith("ScraperError")
