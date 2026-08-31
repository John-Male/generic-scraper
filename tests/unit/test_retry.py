"""Unit tests for retry-with-backoff execution."""

from __future__ import annotations

import pytest

from generic_scraper.config import RetryPolicy
from generic_scraper.errors import FetchError, TransientFetchError
from generic_scraper.retry import RetryRecorder, call_with_retry


def test_returns_immediately_on_success() -> None:
    recorder = RetryRecorder()

    result = call_with_retry(lambda: "ok", RetryPolicy(attempts=3), recorder=recorder)

    assert result == "ok"
    assert recorder.attempts == 1
    assert recorder.sleeps == []


def test_retries_until_success() -> None:
    calls = {"n": 0}

    def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise TransientFetchError("boom")
        return "ok"

    recorder = RetryRecorder()
    result = call_with_retry(flaky, RetryPolicy(attempts=5), recorder=recorder)

    assert result == "ok"
    assert recorder.attempts == 3


@pytest.mark.parametrize("attempts", [3, 5])
def test_gives_up_after_configured_attempts(attempts: int) -> None:
    recorder = RetryRecorder()
    slept: list[float] = []

    def always_fails() -> str:
        raise TransientFetchError("boom")

    with pytest.raises(FetchError, match=f"{attempts} attempt"):
        call_with_retry(
            always_fails,
            RetryPolicy(attempts=attempts, backoff="exponential"),
            sleep=slept.append,
            recorder=recorder,
        )

    assert recorder.attempts == attempts
    assert slept == recorder.sleeps
    assert len(recorder.sleeps) == attempts - 1


def test_exponential_backoff_doubles_the_delay() -> None:
    recorder = RetryRecorder()

    def always_fails() -> str:
        raise TransientFetchError("boom")

    with pytest.raises(FetchError):
        call_with_retry(
            always_fails,
            RetryPolicy(attempts=4, backoff="exponential"),
            sleep=lambda _s: None,
            recorder=recorder,
        )

    assert recorder.sleeps == [1.0, 2.0, 4.0]
