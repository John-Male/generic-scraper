"""The ``ScraperType`` configuration object.

A caller hands the scraper a plain mapping (usually loaded from YAML) describing
which engine, browser, parser, proxy, and retry policy to use. This module turns
that mapping into a validated, typed value object. It performs no IO beyond
reading a YAML file and knows nothing about engines or parsers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

DEFAULT_ENGINE = "requests"
DEFAULT_PROCESSING_TYPE = "beautifulsoup"


@dataclass(frozen=True)
class RetryPolicy:
    """How many fetch attempts to make and how to space them out."""

    attempts: int = 1
    backoff: str = "exponential"

    @classmethod
    def from_value(cls, value: Any) -> RetryPolicy:
        if value is None:
            return cls()
        if isinstance(value, RetryPolicy):
            return value
        if not isinstance(value, dict):
            raise ValueError("retry policy must be a mapping")
        unknown = set(value) - {"attempts", "backoff"}
        if unknown:
            raise ValueError(f"unknown retry policy key: {sorted(unknown)[0]!r}")
        attempts = int(value.get("attempts", cls.attempts))
        if attempts < 1:
            raise ValueError("retry attempts must be at least 1")
        backoff = str(value.get("backoff", cls.backoff))
        return cls(attempts=attempts, backoff=backoff)


_TRUE = {"true", "yes", "1", "on"}
_FALSE = {"false", "no", "0", "off", ""}

_KNOWN_KEYS = {
    "scraper_engine",
    "browser_type",
    "processing_type",
    "secondary",
    "use_proxy",
    "proxy_url",
    "proxy_port",
    "proxy_pass_key",
    "proxy_pass_val",
    "retry",
}


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in _TRUE:
        return True
    if text in _FALSE:
        return False
    raise ValueError(f"cannot read {value!r} as a boolean")


@dataclass(frozen=True)
class ScraperType:
    """A validated scraper configuration."""

    scraper_engine: str = DEFAULT_ENGINE
    browser_type: str | None = None
    processing_type: str = DEFAULT_PROCESSING_TYPE
    secondary: str | None = None
    use_proxy: bool = False
    proxy_url: str | None = None
    proxy_port: int | None = None
    proxy_pass_key: str | None = None
    proxy_pass_val: str | None = None
    retry: RetryPolicy = field(default_factory=RetryPolicy)

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> ScraperType:
        data = dict(raw or {})
        unknown = set(data) - _KNOWN_KEYS
        if unknown:
            raise ValueError(f"unknown ScraperType key: {sorted(unknown)[0]!r}")

        return cls(
            scraper_engine=str(data.get("scraper_engine", DEFAULT_ENGINE)),
            browser_type=_opt_str(data.get("browser_type")),
            processing_type=str(data.get("processing_type", DEFAULT_PROCESSING_TYPE)),
            secondary=_opt_str(data.get("secondary")),
            use_proxy=_as_bool(data.get("use_proxy", False)),
            proxy_url=_opt_str(data.get("proxy_url")),
            proxy_port=_opt_int(data.get("proxy_port")),
            proxy_pass_key=_opt_str(data.get("proxy_pass_key")),
            proxy_pass_val=_opt_str(data.get("proxy_pass_val")),
            retry=RetryPolicy.from_value(data.get("retry")),
        )

    @classmethod
    def from_yaml(cls, path: str | Path) -> ScraperType:
        loaded = yaml.safe_load(Path(path).read_text()) or {}
        if not isinstance(loaded, dict):
            raise ValueError(f"{path}: top-level YAML must be a mapping")
        return cls.from_dict(loaded)

    @property
    def proxy_endpoint(self) -> str | None:
        """``"host:port"`` when a proxy host is configured, else ``None``."""

        if not self.use_proxy or not self.proxy_url:
            return None
        if self.proxy_port is None:
            return self.proxy_url
        return f"{self.proxy_url}:{self.proxy_port}"

    @property
    def proxy_header(self) -> tuple[str, str] | None:
        """The ``(key, value)`` auth header for proxied requests, if any."""

        if self.proxy_pass_key is None:
            return None
        return (self.proxy_pass_key, self.proxy_pass_val or "")


def _opt_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _opt_int(value: Any) -> int | None:
    return None if value is None else int(value)
