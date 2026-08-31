# Using generic-scraper

`generic-scraper` turns a `ScraperType` configuration into a ready scraper that
fetches a page and parses it, with engine fallback, proxy support, retries, and
sharded distributed execution. It never touches the network on its own in tests
or via the CLI's QA affordances — an in-process fake platform serves canned
pages.

## Library

```python
from generic_scraper.config import ScraperType
from generic_scraper.engines.fake_platform import FakePlatform
from generic_scraper.scraper import Scraper

config = ScraperType.from_yaml("fixtures/configs/requests.yaml")
platform = FakePlatform.build(page_html="<title>Hello</title>")
scraper = Scraper(config, platform).initialize()

document = scraper.fetch("https://example.com/page")
print(document.title)          # "Hello"
print(scraper.engine_name)     # "requests"
print(scraper.fallback_chain)  # ("requests",)
```

A production caller supplies a live platform instead of `FakePlatform`; the
`Scraper` API is identical.

## ScraperType keys

| Key | Meaning | Default |
|-----|---------|---------|
| `scraper_engine` | `requests`, `playwright`, or `selenium` | `requests` |
| `browser_type` | `chrome` / `firefox`, for browser engines | none |
| `processing_type` | `beautifulsoup`, `lxml`, `html.parser`, `regex` | `beautifulsoup` |
| `secondary` | engine to try if the primary cannot start | none |
| `use_proxy` | route fetches through a proxy | `false` |
| `proxy_url`, `proxy_port` | proxy host and port | none |
| `proxy_pass_key`, `proxy_pass_val` | auth header sent on proxied requests | none |
| `retry` | `{attempts: N, backoff: exponential}` | `{attempts: 1, backoff: exponential}` |

`proxy_pass_val` is a secret: it is sent as a request header but never logged and
is redacted to `***` in `describe` output. Fixtures use obvious dummy values.

### Engine fallback

The primary engine name must be known; an unknown name raises
`UnsupportedScraperEngineError`. A known engine that is unavailable or fails to
start falls back to `secondary` (if set) and then to `requests`. If nothing can
start, `NoEngineAvailableError` names every engine that was tried.

### Retries

`Scraper.fetch` retries transient fetch errors up to `retry.attempts` times with
exponential backoff. The sleep is injectable, so tests never wait. When every
attempt fails, `FetchError` is raised naming the attempt count.

## Command-line interface

```
python -m generic_scraper <command> [options]
```

Run it with `src` on the path (`PYTHONPATH=src python -m generic_scraper …`) or
after `pip install -e .`.

Every command reads `--config PATH` (a YAML `ScraperType`), prints one JSON
object to stdout and exits `0` on success. On a handled error it prints nothing
to stdout, writes a message beginning with the error class name to stderr, and
exits non-zero.

| Command | Purpose |
|---------|---------|
| `describe` | Resolve the config and print the scraper plan. |
| `fetch` | Initialize, fetch one URL, parse it, print a document summary. |
| `run` | Schedule a sharded job through the fake orchestrator. |

### No-network affordances

These flags let a caller reach conditions the environment will not produce:

| Flag | Effect |
|------|--------|
| `--fixture PATH` | `fetch` / `run` read this saved page instead of the network. |
| `--engine-unavailable NAME` | Treat engine `NAME` as not installed. |
| `--engine-start-failure NAME` | Engine `NAME` is installed but fails to start. |
| `--transient-errors N` | The next `N` fetch attempts raise a transient error. |
| `--report-attempts` | `fetch` also reports the number of fetch attempts. |
| `--print-request-headers` | `fetch` also reports outbound headers (values redacted). |
| `--shards N` | `run` splits the job into `N` shards. |
| `--artifact-dir DIR` | `run` writes each shard's parsed artifact under `DIR`. |
| `--artifact-store DIR` | `run` uploads finished artifacts to this fake store. |
| `--job-resources gpu=BOOL,memory=SZ` | Resource request the job asks for. |
| `--node-capacity gpu=BOOL,mem=SZ` | Capacities the fake nodes advertise. |
