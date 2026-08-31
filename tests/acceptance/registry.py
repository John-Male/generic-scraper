"""Step-handler registry for the acceptance runtime.

A handler registers a regex against *resolved* step text (placeholders already
substituted with example values). Named groups in the pattern are passed to the
handler as keyword arguments. Exactly one handler must match a step; zero or
more than one is a failure, which is how an undefined step fails the build.
"""

from __future__ import annotations

import re
from collections.abc import Callable

Handler = Callable[..., None]


class StepError(AssertionError):
    """Raised for an unsupported, ambiguous, or failed step."""


_HANDLERS: list[tuple[re.Pattern[str], Handler]] = []


def step(pattern: str) -> Callable[[Handler], Handler]:
    compiled = re.compile(pattern)

    def register(fn: Handler) -> Handler:
        _HANDLERS.append((compiled, fn))
        return fn

    return register


def match(text: str) -> tuple[Handler, dict[str, str]]:
    found: list[tuple[Handler, dict[str, str]]] = []
    for pattern, handler in _HANDLERS:
        hit = pattern.match(text)
        if hit and hit.end() == len(text):
            found.append((handler, hit.groupdict()))
    if not found:
        raise StepError(f"unsupported step: {text!r}")
    if len(found) > 1:
        names = ", ".join(h.__name__ for h, _ in found)
        raise StepError(f"ambiguous step {text!r} matched: {names}")
    return found[0]


def clear() -> None:
    """Drop every registered handler. For test isolation only."""

    _HANDLERS.clear()
