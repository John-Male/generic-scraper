"""Unit tests for ScraperType configuration parsing."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from generic_scraper.config import RetryPolicy, ScraperType


def test_empty_config_uses_defaults() -> None:
    cfg = ScraperType.from_dict({})

    assert cfg.scraper_engine == "requests"
    assert cfg.browser_type is None
    assert cfg.processing_type == "beautifulsoup"
    assert cfg.secondary is None
    assert cfg.use_proxy is False
    assert cfg.retry == RetryPolicy(attempts=1, backoff="exponential")


def test_from_dict_reads_engine_and_browser() -> None:
    cfg = ScraperType.from_dict(
        {"scraper_engine": "playwright", "browser_type": "chrome"}
    )

    assert cfg.scraper_engine == "playwright"
    assert cfg.browser_type == "chrome"


def test_use_proxy_accepts_string_true_from_gherkin() -> None:
    cfg = ScraperType.from_dict({"use_proxy": "true"})

    assert cfg.use_proxy is True


def test_use_proxy_accepts_real_bool_from_yaml() -> None:
    cfg = ScraperType.from_dict({"use_proxy": False})

    assert cfg.use_proxy is False


def test_proxy_port_is_coerced_to_int() -> None:
    cfg = ScraperType.from_dict(
        {"use_proxy": True, "proxy_url": "http://proxy.example", "proxy_port": "8080"}
    )

    assert cfg.proxy_port == 8080
    assert cfg.proxy_endpoint == "http://proxy.example:8080"


def test_proxy_endpoint_without_a_port_is_just_the_url() -> None:
    cfg = ScraperType.from_dict(
        {"use_proxy": True, "proxy_url": "http://proxy.example"}
    )

    assert cfg.proxy_endpoint == "http://proxy.example"


def test_proxy_endpoint_is_none_without_proxy() -> None:
    assert ScraperType.from_dict({}).proxy_endpoint is None


def test_proxy_header_pair_is_exposed_when_set() -> None:
    cfg = ScraperType.from_dict(
        {
            "use_proxy": True,
            "proxy_pass_key": "X-Proxy-Auth",
            "proxy_pass_val": "dummy-token-abc",
        }
    )

    assert cfg.proxy_header == ("X-Proxy-Auth", "dummy-token-abc")


def test_proxy_header_is_none_without_pass_key() -> None:
    assert ScraperType.from_dict({"use_proxy": True}).proxy_header is None


def test_retry_policy_is_read_from_nested_mapping() -> None:
    cfg = ScraperType.from_dict({"retry": {"attempts": "5", "backoff": "exponential"}})

    assert cfg.retry == RetryPolicy(attempts=5, backoff="exponential")


def test_use_proxy_accepts_string_false_from_gherkin() -> None:
    assert ScraperType.from_dict({"use_proxy": "no"}).use_proxy is False


def test_use_proxy_rejects_an_unreadable_value() -> None:
    with pytest.raises(ValueError, match="cannot read"):
        ScraperType.from_dict({"use_proxy": "maybe"})


def test_unknown_key_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown ScraperType key"):
        ScraperType.from_dict({"nonsense": 1})


def test_from_yaml_reads_a_committed_fixture(tmp_path: Path) -> None:
    path = tmp_path / "cfg.yaml"
    path.write_text(
        textwrap.dedent(
            """
            scraper_engine: selenium
            browser_type: firefox
            """
        )
    )

    cfg = ScraperType.from_yaml(path)

    assert cfg.scraper_engine == "selenium"
    assert cfg.browser_type == "firefox"


def test_from_yaml_treats_empty_file_as_empty_config(tmp_path: Path) -> None:
    path = tmp_path / "empty.yaml"
    path.write_text("{}\n")

    assert ScraperType.from_yaml(path).scraper_engine == "requests"
