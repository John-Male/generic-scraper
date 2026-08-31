"""The default engine: fetch over HTTP with no browser.

The actual HTTP call is delegated to an injected :class:`HttpTransport`. In
production that is :func:`live_transport` (the ``requests`` library); in tests it
is a fake. The engine itself only assembles the request and normalises the
response.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from generic_scraper.engines.base import REQUESTS, FetchRequest, RawResponse
from generic_scraper.errors import TransientFetchError


@dataclass(frozen=True)
class HttpResult:
    status_code: int
    text: str


class HttpTransport(Protocol):
    """A minimal synchronous HTTP client."""

    def get(
        self, url: str, headers: dict[str, str], proxy: str | None
    ) -> HttpResult:
        ...


class RequestsEngine:
    """Fetches pages with a plain HTTP client."""

    name = REQUESTS

    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    def fetch(self, request: FetchRequest) -> RawResponse:
        result = self._transport.get(request.url, dict(request.headers), request.proxy)
        if result.status_code >= 500:
            raise TransientFetchError(
                f"TransientFetchError: {request.url} returned {result.status_code}"
            )
        return RawResponse(
            url=request.url,
            status_code=result.status_code,
            html=result.text,
            request_headers=dict(request.headers),
        )


def live_transport() -> HttpTransport:  # pragma: no cover - exercised only live
    """A transport backed by the ``requests`` library."""

    import requests

    class _RequestsTransport:
        def get(
            self, url: str, headers: dict[str, str], proxy: str | None
        ) -> HttpResult:
            proxies = {"http": proxy, "https": proxy} if proxy else None
            response = requests.get(
                url, headers=headers, proxies=proxies, timeout=30
            )
            return HttpResult(response.status_code, response.text)

    return _RequestsTransport()
