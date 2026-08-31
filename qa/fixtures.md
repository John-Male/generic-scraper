# Fixtures required by the QA suite

All committed under `fixtures/`. No fixture is fetched at test time.

| File                          | Purpose                                                        |
|-------------------------------|---------------------------------------------------------------|
| `fixtures/test_page.html`     | Minimal HTML page with `<title>Test Page</title>` and a body.  |
| `fixtures/configs/empty.yaml` | `{}` — empty ScraperType.                                      |
| `fixtures/configs/requests.yaml` | `scraper_engine: requests`.                                 |
| `fixtures/configs/playwright_chrome.yaml` | `scraper_engine: playwright`, `browser_type: chrome`. |
| `fixtures/configs/selenium_firefox.yaml`  | `scraper_engine: selenium`, `browser_type: firefox`. |
| `fixtures/configs/proxy.yaml` | `use_proxy: true`, `proxy_url: http://proxy.example`, `proxy_port: 8080`. |
| `fixtures/configs/proxy_header.yaml` | `use_proxy: true`, `proxy_pass_key: X-Proxy-Auth`, `proxy_pass_val: dummy-token-abc`. |
| `fixtures/configs/selenium_secondary.yaml` | `scraper_engine: selenium`, `secondary: requests`. |
| `fixtures/configs/retry.yaml`  | `scraper_engine: requests` plus a retry policy of 3 attempts with exponential backoff. |
| `fixtures/configs/retry_5.yaml` | `scraper_engine: requests` plus a retry policy of 5 attempts with exponential backoff. |
| `fixtures/configs/unknown_engine.yaml` | `scraper_engine: unknown`.                            |

The feature files fix the retry *behavior* (attempt count, backoff kind) but
not the config key names for it — those are the architect's to define. QA
creates `fixtures/configs/retry.yaml` and `fixtures/configs/retry_5.yaml`
(the per-attempt-count variants the procedures need) against the finalized
`ScraperType` schema — `retry: {attempts: N, backoff: exponential}` — and keeps
them in step with `qa/08_error_handling_and_retries.md`.

`proxy_pass_val` in every fixture is an obvious dummy. No real secret is ever
committed.
