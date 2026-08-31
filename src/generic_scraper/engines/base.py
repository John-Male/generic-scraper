"""The engine interface every fetch adapter implements.

An *engine* is the thing that turns a URL into raw HTML. Each concrete engine
(requests, Playwright, Selenium) is an adapter behind this interface. High-level
policy depends only on :class:`Engine`, never on a concrete engine or its
library.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

REQUESTS = "requests"
PLAYWRIGHT = "playwright"
SELENIUM = "selenium"

KNOWN_ENGINES = (REQUESTS, PLAYWRIGHT, SELENIUM)
BROWSER_ENGINES = (PLAYWRIGHT, SELENIUM)


@dataclass(frozen=True)
class FetchRequest:
    """Everything an engine needs to make one fetch."""

    url: str
    headers: dict[str, str] = field(default_factory=dict)
    proxy: str | None = None


@dataclass(frozen=True)
class RawResponse:
    """The raw result of a fetch, before parsing."""

    url: str
    status_code: int
    html: str
    request_headers: dict[str, str] = field(default_factory=dict)


@runtime_checkable
class Engine(Protocol):
    """Fetches a URL and returns raw HTML."""

    name: str

    def fetch(self, request: FetchRequest) -> RawResponse:
        """Fetch ``request.url`` and return the raw response."""
        ...
