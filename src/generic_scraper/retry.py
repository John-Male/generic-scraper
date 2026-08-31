"""Retry policy execution with an injectable clock.

``call_with_retry`` runs an operation up to ``policy.attempts`` times, sleeping
between attempts according to the backoff strategy. The sleep is delegated to an
injected callable so tests never wait on the wall clock.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TypeVar

from generic_scraper.errors import FetchError, TransientFetchError
from generic_scraper.retry_policy import RetryPolicy

T = TypeVar("T")

Sleeper = Callable[[float], None]


def no_sleep(_seconds: float) -> None:
    """A :data:`Sleeper` that returns immediately. The test default."""

    return None


@dataclass
class RetryRecorder:
    """Captures how a retried call behaved, for assertions and reporting."""

    attempts: int = 0
    sleeps: list[float] = field(default_factory=list)


def _delay_for(policy: RetryPolicy, attempt_index: int) -> float:
    if policy.backoff == "exponential":
        return float(2**attempt_index)
    if policy.backoff == "linear":
        return float(attempt_index + 1)
    return 0.0


def call_with_retry(
    operation: Callable[[], T],
    policy: RetryPolicy,
    *,
    sleep: Sleeper = no_sleep,
    recorder: RetryRecorder | None = None,
) -> T:
    """Run ``operation``, retrying on :class:`TransientFetchError`.

    Retries up to ``policy.attempts`` total attempts. If every attempt raises a
    transient error, a :class:`FetchError` is raised naming the attempt count.
    """

    rec = recorder or RetryRecorder()
    last_error: TransientFetchError | None = None

    for attempt_index in range(policy.attempts):
        rec.attempts += 1
        try:
            return operation()
        except TransientFetchError as error:
            last_error = error
            if attempt_index + 1 < policy.attempts:
                delay = _delay_for(policy, attempt_index)
                rec.sleeps.append(delay)
                sleep(delay)

    raise FetchError(
        f"FetchError: fetch failed after {rec.attempts} attempt(s): {last_error}"
    )
