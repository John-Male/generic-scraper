# Testing

One runner, `pytest`, executes the unit tests and the `pytest-bdd` acceptance
scenarios together. No test touches the network, launches a browser, or sleeps
on the wall clock.

## Standard verification

Run, in order:

```
pytest                 # unit tests + acceptance scenarios
pytest -m property     # property-based tests (see below)
ruff check .
mypy src
```

`pytest` alone also collects the property tests; `-m property` runs only them,
which is the explicit gate the architect, hardender, and QA roles apply.

## Property tests

`tests/property/` checks invariants over many randomised inputs. The project's
dependency allowlist has no room for Hypothesis, so `tests/property/framework.py`
supplies a minimal `for_all(strategy, prop)` helper: it draws pseudo-random
values from a *strategy* callable and asserts a property for each. The seed is
fixed, so a failing run names the case and input to replay by hand.

Properties currently covered:

- **config** — parsing is deterministic; a parsed config survives a YAML
  round trip; boolean words map by their truth set; `proxy_endpoint` and
  `proxy_header` stay consistent with their parts.
- **retry** — attempts are always one more than recorded sleeps; recorded and
  actual sleeps agree; a call succeeds exactly when its failures fit the budget;
  backoff delays are non-negative and non-decreasing.
- **orchestrator** — memory units scale as documented and ignore case and
  surrounding space; node satisfaction is monotonic in capacity; every shard
  lands on a distinct node and uploads once.
- **parsers** — all four processing types recover the same title, keep body
  text, drop script/style, preserve raw HTML, and are idempotent.
- **engine resolution** — resolution ends on a usable engine or raises
  `NoEngineAvailableError`; the fallback chain never repeats a candidate and
  every skipped candidate was genuinely unusable; resolution is deterministic.
