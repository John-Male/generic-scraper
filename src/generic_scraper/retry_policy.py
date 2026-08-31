"""The ``RetryPolicy`` value object.

How many fetch attempts to make and how to space them out. Kept apart from
:mod:`generic_scraper.config` so both the configuration object and the retry
executor can depend on it without depending on each other.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_RETRY_KEYS = {"attempts", "backoff"}


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
        unknown = set(value) - _RETRY_KEYS
        if unknown:
            raise ValueError(f"unknown retry policy key: {sorted(unknown)[0]!r}")
        attempts = int(value.get("attempts", cls.attempts))
        if attempts < 1:
            raise ValueError("retry attempts must be at least 1")
        backoff = str(value.get("backoff", cls.backoff))
        return cls(attempts=attempts, backoff=backoff)
