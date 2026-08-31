"""Unit tests for the RetryPolicy value object."""

from __future__ import annotations

import pytest

from generic_scraper.retry_policy import RetryPolicy


def test_none_yields_the_default_policy() -> None:
    assert RetryPolicy.from_value(None) == RetryPolicy(attempts=1)


def test_a_mapping_is_read_and_coerced() -> None:
    policy = RetryPolicy.from_value({"attempts": "5", "backoff": "linear"})

    assert policy == RetryPolicy(attempts=5, backoff="linear")


def test_an_existing_policy_passes_through_unchanged() -> None:
    policy = RetryPolicy(attempts=3, backoff="linear")

    assert RetryPolicy.from_value(policy) is policy


def test_a_non_mapping_is_rejected() -> None:
    with pytest.raises(ValueError, match="must be a mapping"):
        RetryPolicy.from_value("fast")


def test_an_unknown_key_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown retry policy key: 'jitter'"):
        RetryPolicy.from_value({"jitter": 1})


def test_fewer_than_one_attempt_is_rejected() -> None:
    with pytest.raises(ValueError, match="at least 1"):
        RetryPolicy.from_value({"attempts": 0})
