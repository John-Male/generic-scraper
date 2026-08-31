# QA — 07 Distributed execution, artifact upload, and node affinity

Covers scenarios `distributed_execution_and_artifacts-1..3`. All runs use the
fake orchestrator (`--orchestrator fake`, the default). No real worker node.

## QA-7.1 — Job runs across N distinct workers, each producing an artifact

For each `shards` in `3`, `5`:

1. Config with `scraper_engine: requests`.
2. Run:
   `python -m generic_scraper run --config <config> --url https://example.com/test-page --fixture fixtures/test_page.html --shards <shards> --artifact-dir <tmpdir>`
3. Expect exit `0`. Assert on stdout JSON:
   - `.shards == <shards>`
   - `.worker_nodes` has `<shards>` entries, all distinct.
   - `.artifacts` has `<shards>` entries; each named file exists under
     `<tmpdir>`.

## QA-7.2 — Each finished shard uploads its artifact to the store

1. Run the same command as QA-7.1 with `--shards 3` and
   `--artifact-store <storedir>`.
2. Expect exit `0`. Assert:
   - `.uploaded` lists `parsed_result.json` once per shard.
   - `<storedir>` contains one `parsed_result.json` per shard (namespaced by
     worker node so they do not collide).

## QA-7.3 — Job is placed on a node satisfying resource constraints

1. Config with `browser_type: chrome`.
2. Run:
   `python -m generic_scraper run --config <config> --url https://example.com/test-page --fixture fixtures/test_page.html --shards 1 --artifact-dir <tmpdir> --job-resources gpu=false,memory=2GB --node-capacity gpu=false,mem=4GB`
3. Expect exit `0`. Assert `.placement.gpu == false`,
   `.placement.memory == "2GB"`, and `.placement.node` is one of the
   advertised nodes.
4. Re-run with `--node-capacity gpu=false,mem=1GB` (too small). Expect
   non-zero exit and stderr starting with a descriptive placement error
   naming the unsatisfied constraint.
