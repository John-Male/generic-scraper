"""Property tests for ``ScraperType`` parsing and its derived views."""

from __future__ import annotations

import random

import pytest
import yaml

from generic_scraper.config import ScraperType
from tests.property.framework import for_all, token, words

pytestmark = pytest.mark.property

_TRUE_WORDS = ("true", "yes", "1", "on", "True", "YES")
_FALSE_WORDS = ("false", "no", "0", "off", "", "False", "NO")
_ENGINES = ("requests", "playwright", "selenium")
_PROCESSORS = ("beautifulsoup", "lxml", "html.parser", "regex")
_BACKOFFS = ("exponential", "linear", "none")


def _config_dict(rng: random.Random) -> dict[str, object]:
    data: dict[str, object] = {
        "scraper_engine": rng.choice(_ENGINES),
        "processing_type": rng.choice(_PROCESSORS),
        "retry": {
            "attempts": rng.randint(1, 10),
            "backoff": rng.choice(_BACKOFFS),
        },
    }
    if rng.random() < 0.5:
        data["browser_type"] = rng.choice(("chrome", "firefox", "webkit"))
    if rng.random() < 0.5:
        data["secondary"] = rng.choice(_ENGINES)
    if rng.random() < 0.6:
        data["use_proxy"] = True
        data["proxy_url"] = f"http://{token(rng)}.example"
        if rng.random() < 0.7:
            data["proxy_port"] = rng.randint(1, 65535)
        if rng.random() < 0.7:
            data["proxy_pass_key"] = f"X-{token(rng)}"
            data["proxy_pass_val"] = token(rng)
    return data


def test_parsing_is_deterministic() -> None:
    for_all(_config_dict, lambda d: _assert_stable(d))


def _assert_stable(data: dict[str, object]) -> None:
    assert ScraperType.from_dict(dict(data)) == ScraperType.from_dict(dict(data))


def test_from_dict_is_idempotent_through_yaml() -> None:
    """A parsed config, dumped to YAML and reloaded, parses back to itself."""

    def prop(data: dict[str, object]) -> None:
        first = ScraperType.from_dict(dict(data))
        round_tripped = ScraperType.from_yaml_text(_dump(first))
        assert round_tripped == first

    for_all(_config_dict, prop)


def _dump(cfg: ScraperType) -> str:
    body: dict[str, object] = {
        "scraper_engine": cfg.scraper_engine,
        "processing_type": cfg.processing_type,
        "use_proxy": cfg.use_proxy,
        "retry": {"attempts": cfg.retry.attempts, "backoff": cfg.retry.backoff},
    }
    optional = (
        "browser_type", "secondary", "proxy_url", "proxy_port",
        "proxy_pass_key", "proxy_pass_val",
    )
    for key in optional:
        value = getattr(cfg, key)
        if value is not None:
            body[key] = value
    return str(yaml.safe_dump(body))


def test_boolean_words_parse_by_their_truth_set() -> None:
    def prop(pair: tuple[str, bool]) -> None:
        text, expected = pair
        assert ScraperType.from_dict({"use_proxy": text}).use_proxy is expected

    def strategy(rng: random.Random) -> tuple[str, bool]:
        if rng.random() < 0.5:
            return rng.choice(_TRUE_WORDS), True
        return rng.choice(_FALSE_WORDS), False

    for_all(strategy, prop)


def test_proxy_endpoint_is_consistent_with_its_parts() -> None:
    def prop(data: dict[str, object]) -> None:
        cfg = ScraperType.from_dict(dict(data))
        endpoint = cfg.proxy_endpoint
        if not cfg.use_proxy or not cfg.proxy_url:
            assert endpoint is None
            return
        assert endpoint is not None and endpoint.startswith(cfg.proxy_url)
        if cfg.proxy_port is not None:
            assert endpoint == f"{cfg.proxy_url}:{cfg.proxy_port}"

    for_all(_config_dict, prop)


def test_proxy_header_round_trips_key_and_value() -> None:
    def prop(data: dict[str, object]) -> None:
        cfg = ScraperType.from_dict(dict(data))
        header = cfg.proxy_header
        if cfg.proxy_pass_key is None:
            assert header is None
        else:
            assert header == (cfg.proxy_pass_key, cfg.proxy_pass_val or "")

    for_all(_config_dict, prop)


def test_unknown_key_is_always_rejected() -> None:
    def prop(name: str) -> None:
        with pytest.raises(ValueError, match="unknown ScraperType key"):
            ScraperType.from_dict({name: 1})

    for_all(
        lambda rng: "z" + words(rng, low=1, high=2).replace(" ", "_"),
        prop,
        cases=50,
    )
