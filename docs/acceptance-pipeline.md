# Acceptance pipeline

This project installs the Acceptance Pipeline Specification (APS) pipeline. The
eight `.feature` files in `features/` are the source of truth for behaviour.

## Flow

```
features/*.feature
  -> gherkin-parser            (APS-supplied)      -> tests/acceptance/ir/*.json
  -> acceptance-entrypoint-generator (this repo)   -> tests/acceptance/generated/
  -> pytest                                        -> pass / fail
```

- **`gherkin-parser`** is the APS tool. We do not reimplement it.
- **`scripts/acceptance-entrypoint-generator <json-ir> <out-dir>`** reads one IR
  file and writes a pytest module that embeds that IR and runs every scenario
  execution it represents, plus a metadata file under `metadata/` with an
  `implementation_hash` over the generated file.
- **`tests/acceptance/runtime.py`** expands IR into executions (one per example
  row, background steps prepended), resolves `<placeholders>` from the example
  row, and routes each resolved step to a handler.
- **`tests/acceptance/steps/`** holds the step handlers. Each registers a regex
  against resolved step text; named groups become handler keyword arguments.
  Exactly one handler must match a step — zero or many is a build failure, so an
  undefined step fails the build rather than pending.

There is one test runner: `pytest`. The generated tests are committed, so
`pytest` alone runs unit tests and acceptance scenarios together.

## Commands

```sh
# Regenerate IR + entry points from the features, then run them:
scripts/run-acceptance.sh

# Run everything (unit + already-generated acceptance):
pytest
```

Regenerate and commit the generated tests whenever a `.feature` file changes.
Never edit a `.feature` to make a scenario pass; hand it back to the specifier
with the scenario name and why.

## Notes for reviewers

`pytest-bdd` is listed as a dev dependency but is not used directly: APS requires
that generated entry points load the JSON IR and never parse the source Gherkin,
which `pytest-bdd`'s `scenarios()` does. The APS runtime satisfies the same
intent — BDD scenarios executed under a single `pytest` runner, with step
definitions in `tests/acceptance/steps/`.
