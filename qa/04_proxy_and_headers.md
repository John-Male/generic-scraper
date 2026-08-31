# QA — 04 Proxy configuration and header pass key

Covers scenarios `proxy_and_headers-1`, `proxy_and_headers-2`.

## QA-4.1 — Proxy URL and port are combined into one endpoint

For each `(proxy_url, proxy_port)` in
`(http://proxy.example, 8080)`, `(http://proxy.internal, 3128)`:

1. Config with `use_proxy: true`, `proxy_url: <proxy_url>`,
   `proxy_port: <proxy_port>`.
2. Run: `python -m generic_scraper describe --config <config>`
3. Expect exit `0`. Assert `.proxy == "<proxy_url>:<proxy_port>"`.

## QA-4.2 — Pass key header is attached to proxied requests

For each `(pass_key, pass_val)` in
`(X-Proxy-Auth, dummy-token-abc)`, `(X-Auth-Token, dummy-token-xyz)`:

1. Config with `use_proxy: true`, `proxy_pass_key: <pass_key>`,
   `proxy_pass_val: <pass_val>`.
2. Run: `python -m generic_scraper describe --config <config>`
3. Expect exit `0`. Assert:
   - `.proxy_header` starts with `"<pass_key>: "`.
   - The pass value is **not** echoed in full; `.proxy_header` ends with `***`.
4. Run `fetch` with `--fixture fixtures/test_page.html` and
   `--print-request-headers`. Assert the recorded request carried the header
   `"<pass_key>"` and that the CLI output redacts its value.

## QA-4.3 — The secret never appears in output

Grep the full stdout+stderr of every command in QA-4.2 for the literal
`proxy_pass_val` value. It must not appear.
