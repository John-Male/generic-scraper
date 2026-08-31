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

## Mutation hardening

Two mutation tools check that a passing suite actually pins behaviour. They are
the hardender's gate and run separately from `pytest`.

### Source mutation

```
python -m mutmut run --paths-to-mutate src/generic_scraper/<file>.py
```

Run one file at a time (`mutmut` 2.5.1 has no worker-pool flag). `mutmut run
--use-patch-file <diff>` restricts a run to changed lines; the first hardening
pass covered the whole of `src/generic_scraper/`, which was entirely new since
the task base. `tests/hardening/` holds the tests written to kill mutants the
unit, acceptance, and property suites leave alive -- value-object
immutability, exact zero-argument defaults, the `>= 500` transient boundary,
`_TitleTextExtractor` script/style skipping, and the CLI parsing helpers. Run
them alone with `pytest -m hardening`.

The mutants that still survive are equivalent -- a change with no
test-observable effect -- and are left rather than chased with brittle
assertions:

- **Annotation operator swaps** (`str | None` -> `str & None`). With
  `from __future__ import annotations` the annotation is a string and is never
  evaluated.
- **String-literal wrappers** (`"msg"` -> `"XXmsgXX"`) on error text, argparse
  `help=` / `prog=`, and internal dict keys. The message stays accurate,
  argparse help is not behaviour, and the dict keys are only ever read back by
  the same code.
- **`live_transport` internals** and the `if __name__ == "__main__"` guards --
  all under `# pragma: no cover`, live-only code a hermetic suite cannot reach.
- **Fake-platform field defaults** (`transient_errors: int = 0` -> `1`). The
  fakes are always built through `FakePlatform.build(...)`, which passes every
  field explicitly.
- **`@runtime_checkable` removal** on `Engine` / `RenderingEngine`. On CPython
  3.11 the `isinstance` checks in `Scraper` still resolve through the base
  protocol, so the decorator has no observable effect here.

### Acceptance mutation

```
gherkin-mutator --feature features/<f>.feature \
  --generated-dir tests/acceptance/generated \
  --runner-worker "<python> scripts/acceptance-mutation-runner" --level soft
```

`scripts/acceptance-mutation-runner` is the persistent worker adapter: it
expands each mutated IR through `tests/acceptance/runtime.py` and reports a
step failure as a kill. The runner must run under the interpreter that has the
project dependencies installed; `run-acceptance-mutation.sh` picks one.

The run is non-differential on purpose. `gherkin-mutator` can stamp a reuse
manifest into each `.feature` file, but the whole corpus is ~40 mutations and a
full pass takes a few seconds, so the eight hand-written spec files are left
untouched rather than carrying machine-written manifest comments.

Features 01, 03, 05 and 06 kill every mutation. The survivors in 02, 04, 07 and
08 are value-echo or equivalent:

- **Outline value-echo** -- `browser_configuration-1` and both
  `proxy_and_headers` scenarios put the example placeholder in the `Then` as
  well as the `Given` (`Then ... launch "<browser>"`), so a changed example
  value flows into the expectation too. The scenarios still verify assembly
  (endpoint is `host:port`, header is `key: value`); they cannot verify a
  specific value.
- **Redundant example rows** -- `distributed_execution_and_artifacts-1` row
  `| 5 |` and `error_handling_and_retries-1` row `| 5 |` exercise the same path
  as row `| 3 |`.
- **Opaque identifiers** -- `unknown` -> `unknowN` is still an unknown engine;
  `parsed_result.json` -> `parsed_Result.json` is still an opaque name.

Tightening these needs literal expected values in the feature files, which is
the specifier's call.

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
