# QA — 06 End-to-end fetch and parse using configured options

Covers scenario `end_to_end_fetch_parse-1`.

## QA-6.1 — Full pipeline: fetch then parse

Test URL: `https://example.com/test-page`, served from
`fixtures/test_page.html`.

For each `(engine, processor)` in
`(requests, beautifulsoup)`, `(requests, lxml)`,
`(selenium, beautifulsoup)`, `(playwright, html.parser)`:

1. Config with `scraper_engine: <engine>`, `processing_type: <processor>`.
2. Run:
   `python -m generic_scraper fetch --config <config> --fixture fixtures/test_page.html --url https://example.com/test-page`
3. Expect exit `0`. Assert on stdout JSON:
   - `.engine == "<engine>"`
   - `.processor == "<processor>"`
   - `.status == "ok"`
   - `.title == "Test Page"` (the parsed document contains the page title)
4. No real HTTP request and no real browser launch occurred during the run.
