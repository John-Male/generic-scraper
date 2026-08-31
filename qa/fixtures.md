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
| `fixtures/configs/retry3.yaml` | `scraper_engine: requests`, `retry: {attempts: 3, backoff: exponential}`. |
| `fixtures/configs/unknown_engine.yaml` | `scraper_engine: unknown`.                            |

`proxy_pass_val` in every fixture is an obvious dummy. No real secret is ever
committed.
