"""Executable form of ``qa/04_proxy_and_headers.md``.

Covers scenarios proxy_and_headers-1 and proxy_and_headers-2, including the
guarantee that the pass value never appears in command output.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.e2e._cli import PAGE, TEST_URL, run_cli, write_config

ENDPOINTS = [
    ("http://proxy.example", 8080),
    ("http://proxy.internal", 3128),
]
PASS_KEYS = [
    ("X-Proxy-Auth", "dummy-token-abc"),
    ("X-Auth-Token", "dummy-token-xyz"),
]


@pytest.mark.parametrize(("proxy_url", "proxy_port"), ENDPOINTS)
def test_qa_4_1_proxy_url_and_port_are_combined(
    proxy_url: str, proxy_port: int, tmp_path: Path
) -> None:
    config = write_config(
        tmp_path,
        f"use_proxy: true\nproxy_url: {proxy_url}\nproxy_port: {proxy_port}\n",
    )

    result = run_cli("describe", "--config", config)

    assert result.code == 0
    assert result.json["proxy"] == f"{proxy_url}:{proxy_port}"


@pytest.mark.parametrize(("pass_key", "pass_val"), PASS_KEYS)
def test_qa_4_2_and_4_3_pass_key_header_is_attached_and_secret_never_leaks(
    pass_key: str, pass_val: str, tmp_path: Path
) -> None:
    config = write_config(
        tmp_path,
        f"use_proxy: true\nproxy_pass_key: {pass_key}\nproxy_pass_val: {pass_val}\n",
    )

    described = run_cli("describe", "--config", config)
    assert described.code == 0
    header = described.json["proxy_header"]
    assert isinstance(header, str)
    assert header.startswith(f"{pass_key}: ")
    assert header.endswith("***")

    fetched = run_cli(
        "fetch",
        "--config",
        config,
        "--fixture",
        str(PAGE),
        "--url",
        TEST_URL,
        "--print-request-headers",
    )
    assert fetched.code == 0
    recorded = fetched.json["request_headers"]
    assert pass_key in recorded
    assert recorded[pass_key] == "***"

    # QA-4.3: the literal secret must not appear anywhere in either command.
    assert pass_val not in described.combined
    assert pass_val not in fetched.combined
