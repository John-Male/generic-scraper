# QA — 02 Configure browser type for browser-based scraping engines

Covers scenario `browser_configuration-1`.

## QA-2.1 — Browser type is honored per engine

For each `(engine, browser)` in
`(playwright, chrome)`, `(playwright, firefox)`, `(selenium, chrome)`,
`(selenium, firefox)`:

1. Config with `scraper_engine: <engine>` and `browser_type: <browser>`.
2. Run: `python -m generic_scraper describe --config <config>`
3. Expect exit `0`. Assert on stdout JSON:
   - `.engine == "<engine>"`
   - `.browser == "<browser>"`
4. The `describe` run must not launch a real browser process (verify no
   browser binary is spawned; the fake driver records the requested
   `(engine, browser)` pair only).
