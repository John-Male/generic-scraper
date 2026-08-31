"""Property tests for retry-with-backoff execution and the policy object."""

from __future__ import annotations

import random

import pytest

from generic_scraper.errors import FetchError, TransientFetchError
from generic_scraper.retry import RetryRecorder, call_with_retry
from generic_scraper.retry_policy import RetryPolicy
from tests.property.framework import for_all

pytestmark = pytest.mark.property

_BACKOFFS = ("exponential", "linear", "none")


def _scenario(rng: random.Random) -> tuple[RetryPolicy, int]:
    policy = RetryPolicy(
        attempts=rng.randint(1, 12), backoff=rng.choice(_BACKOFFS)
    )
    failures_before_success = rng.randint(0, 15)
    return policy, failures_before_success


def _run(policy: RetryPolicy, failures: int) -> tuple[RetryRecorder, list[float], bool]:
    remaining = {"n": failures}
    slept: list[float] = []

    def operation() -> str:
        if remaining["n"] > 0:
            remaining["n"] -= 1
            raise TransientFetchError("boom")
        return "ok"

    recorder = RetryRecorder()
    raised = False
    try:
        call_with_retry(
            operation, policy, sleep=slept.append, recorder=recorder
        )
    except FetchError:
        raised = True
    return recorder, slept, raised


def test_attempts_are_one_more_than_sleeps() -> None:
    def prop(scenario: tuple[RetryPolicy, int]) -> None:
        recorder, _slept, _raised = _run(*scenario)
        assert recorder.attempts == len(recorder.sleeps) + 1

    for_all(_scenario, prop)


def test_recorded_sleeps_match_what_was_slept() -> None:
    def prop(scenario: tuple[RetryPolicy, int]) -> None:
        recorder, slept, _raised = _run(*scenario)
        assert slept == recorder.sleeps

    for_all(_scenario, prop)


def test_succeeds_iff_failures_fit_within_the_budget() -> None:
    def prop(scenario: tuple[RetryPolicy, int]) -> None:
        policy, failures = scenario
        recorder, _slept, raised = _run(policy, failures)
        if failures < policy.attempts:
            assert not raised
            assert recorder.attempts == failures + 1
        else:
            assert raised
            assert recorder.attempts == policy.attempts

    for_all(_scenario, prop)


def test_delays_are_non_negative_and_non_decreasing() -> None:
    def prop(scenario: tuple[RetryPolicy, int]) -> None:
        policy, _failures = scenario
        recorder, _slept, _raised = _run(policy, policy.attempts)
        assert all(delay >= 0 for delay in recorder.sleeps)
        assert recorder.sleeps == sorted(recorder.sleeps)

    for_all(_scenario, prop)


def test_from_value_normalises_to_at_least_one_attempt() -> None:
    def prop(raw: dict[str, object]) -> None:
        policy = RetryPolicy.from_value(dict(raw))
        assert policy.attempts >= 1
        assert RetryPolicy.from_value(policy) is policy

    def strategy(rng: random.Random) -> dict[str, object]:
        return {
            "attempts": str(rng.randint(1, 20)),
            "backoff": rng.choice(_BACKOFFS),
        }

    for_all(strategy, prop)
