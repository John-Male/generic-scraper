#!/usr/bin/env bash
# Soft acceptance mutation over every feature. Mutates example values in the
# parsed IR and re-runs the generated acceptance entry points through
# scripts/acceptance-mutation-runner; a step failure means the change was
# caught. See docs/testing.md for the surviving-mutant catalogue.
set -euo pipefail

cd "$(dirname "$0")/.."

# The runner adapter must execute under the interpreter that has the project
# dependencies (PyYAML, beautifulsoup4, lxml). gherkin-mutator would otherwise
# spawn it via `/usr/bin/env python3`, which may be a bare interpreter.
pick_python() {
    for cand in "${MUTATION_PYTHON:-}" python python3; do
        [ -n "$cand" ] || continue
        if command -v "$cand" >/dev/null 2>&1 && \
           "$cand" -c 'import yaml, bs4, lxml' >/dev/null 2>&1; then
            command -v "$cand"
            return 0
        fi
    done
    echo "no interpreter with PyYAML/beautifulsoup4/lxml found" >&2
    return 1
}
PYTHON="$(pick_python)"
RUNNER="$PYTHON $(pwd)/scripts/acceptance-mutation-runner"
WORK_DIR="${WORK_DIR:-tmp/acc-mut}"
LEVEL="${LEVEL:-soft}"

status=0
for feature in features/*.feature; do
    stem="$(basename "$feature" .feature)"
    echo "### $stem"
    gherkin-mutator \
        --feature "$feature" \
        --work-dir "$WORK_DIR/$stem" \
        --generated-dir tests/acceptance/generated \
        --runner-worker "$RUNNER" \
        --level "$LEVEL" \
        --status-interval 15s \
        "$@" || status=1
done
exit "$status"
