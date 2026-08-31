"""A tiny dependency-free property-testing helper.

The project's dependency allowlist has no room for Hypothesis, and the
properties worth checking here are small, so this module supplies just enough:
``for_all`` draws pseudo-random values from a *strategy* (a callable taking a
:class:`random.Random`) and asserts a property holds for every draw.

The seed is fixed, so a run is reproducible. On failure the offending input is
attached to the assertion message so it can be replayed by hand.
"""

from __future__ import annotations

import random
import string
from collections.abc import Callable, Sequence
from typing import TypeVar

T = TypeVar("T")

DEFAULT_CASES = 200
DEFAULT_SEED = 20260830

Strategy = Callable[[random.Random], T]


def for_all(
    strategy: Strategy[T],
    prop: Callable[[T], None],
    *,
    cases: int = DEFAULT_CASES,
    seed: int = DEFAULT_SEED,
) -> None:
    """Assert ``prop(value)`` for ``cases`` values drawn from ``strategy``."""

    rng = random.Random(seed)
    for index in range(cases):
        value = strategy(rng)
        try:
            prop(value)
        except AssertionError as failure:
            raise AssertionError(
                f"property failed on case {index} "
                f"(seed={seed}): {value!r}"
            ) from failure


# -- generic strategies ----------------------------------------------------

_WORDS: Sequence[str] = (
    "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "words", "here",
)
_SPACES: Sequence[str] = (" ", "  ", "\t", "\n", " \n ", "\r\n")


def choice(options: Sequence[T]) -> Strategy[T]:
    return lambda rng: rng.choice(list(options))


def words(rng: random.Random, *, low: int = 1, high: int = 8) -> str:
    return " ".join(rng.choice(_WORDS) for _ in range(rng.randint(low, high)))


def whitespace(rng: random.Random) -> str:
    return "".join(rng.choice(_SPACES) for _ in range(rng.randint(0, 4)))


def messy_text(rng: random.Random) -> str:
    """Words wrapped in and separated by arbitrary runs of whitespace."""

    parts = [whitespace(rng)]
    for _ in range(rng.randint(0, 6)):
        parts.append(rng.choice(_WORDS))
        parts.append(whitespace(rng))
    return "".join(parts)


def token(rng: random.Random, *, low: int = 1, high: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits + "-_"
    return "".join(
        rng.choice(alphabet) for _ in range(rng.randint(low, high))
    )
