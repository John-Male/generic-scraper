# End-to-end QA suite — generic-scraper

These procedures verify each feature **through the user interface only**. QA
never imports `generic_scraper` or calls a project function directly. The one
user interface is the command-line entry point:

    python -m generic_scraper <command> [options]

QA converts each `qa/NN_*.md` procedure into an executable script that drives
this CLI and asserts on its **stdout**, **stderr**, and **exit code**.

## Commands

| Command    | Purpose                                                        |
|------------|---------------------------------------------------------------|
| `describe` | Resolve a `ScraperType` config and print the scraper plan.     |
| `fetch`    | Initialize, fetch one URL, parse it, print a document summary. |
| `run`      | Schedule a sharded job through the (fake) orchestrator.        |

All commands take `--config PATH` pointing at a YAML `ScraperType` file. All
commands print a single JSON object to stdout on success and exit `0`. On a
handled error they print nothing to stdout, write a message **beginning with
the error class name** to stderr, and exit non-zero.

## `describe` output shape

```json
{
  "engine": "requests",
  "requested_engine": "playwright",
  "browser": null,
  "processor": "beautifulsoup",
  "proxy": null,
  "proxy_header": null,
  "fallback_chain": ["playwright", "requests"],
  "retry": {"attempts": 1, "backoff": "exponential"}
}
```

- `engine` — the engine that will actually be used after defaults/fallbacks.
- `requested_engine` — what the config asked for (may equal `engine`).
- `browser` — `null` when no browser is configured.
- `proxy` — `"<host>:<port>"` string, or `null`.
- `proxy_header` — `"<key>: <value>"` with the value **redacted to `***`**
  whenever it comes from `proxy_pass_val`; `null` when no pass key is set.
- `fallback_chain` — engines tried, in order, ending with the chosen one.

## `fetch` output shape

```json
{"engine": "requests", "processor": "lxml", "title": "Test Page", "status": "ok"}
```

## `run` output shape

```json
{
  "shards": 3,
  "worker_nodes": ["node-0", "node-1", "node-2"],
  "artifacts": ["node-0/parsed_result.json", "node-1/parsed_result.json",
                "node-2/parsed_result.json"],
  "uploaded": ["parsed_result.json", "parsed_result.json", "parsed_result.json"],
  "placement": {"gpu": false, "memory": "2GB", "node": "node-0"}
}
```

## QA-only user-interface affordances

No network, no real browser, and no real worker node are ever used. These flags
are part of the CLI surface (documented in `--help`) and are the only way QA can
reach conditions the environment will not produce on its own:

| Flag                             | Effect                                                         |
|----------------------------------|---------------------------------------------------------------|
| `--fixture PATH`                 | `fetch`/`run` read this saved HTML/JSON file instead of the network. |
| `--engine-unavailable NAME`      | Treat engine `NAME` as not installed on this node.            |
| `--engine-start-failure NAME`    | Engine `NAME` is installed but fails to start.                |
| `--transient-errors N`           | The next `N` fetch attempts raise a transient network error.  |
| `--report-attempts`              | `fetch` also reports how many fetch attempts were made.       |
| `--print-request-headers`        | `fetch` also reports the outbound request headers (values redacted). |
| `--orchestrator fake`            | `run` schedules on the in-process fake orchestrator (default). |
| `--shards N`                     | `run` splits the job into `N` shards.                         |
| `--artifact-dir DIR`             | `run` writes each shard's parsed artifact under `DIR`.        |
| `--artifact-store DIR`           | `run` uploads finished artifacts to this fake store.          |
| `--job-resources gpu=BOOL,memory=SZ` | Resource request the job asks the orchestrator for.      |
| `--node-capacity gpu=BOOL,mem=SZ`| Capacities the fake orchestrator's nodes advertise.           |

Fixtures live in `fixtures/` and are committed. `qa/fixtures.md` lists the ones
these procedures require.
