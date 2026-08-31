#!/usr/bin/env bash
# Normal acceptance run: parse every feature to JSON IR, generate the pytest
# entry points, then run them. `pytest` alone also runs the committed generated
# tests; this script regenerates them first so they cannot drift from the
# feature files.
set -euo pipefail

cd "$(dirname "$0")/.."

IR_DIR="tests/acceptance/ir"
GEN_DIR="tests/acceptance/generated"
mkdir -p "$IR_DIR" "$GEN_DIR/metadata"

for feature in features/*.feature; do
    stem="$(basename "$feature" .feature)"
    gherkin-parser "$feature" "$IR_DIR/$stem.json"
    scripts/acceptance-entrypoint-generator "$IR_DIR/$stem.json" "$GEN_DIR"
done

exec python -m pytest "$GEN_DIR" "$@"
