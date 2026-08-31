# QA — 01 Initialize Scraper with chosen scraping engine

Covers scenario `initialize_scraper-1`.

## QA-1.1 — Each engine is selected and reported ready

For each `engine` in `requests`, `playwright`, `selenium`:

1. Write a config file with `scraper_engine: <engine>` (or reuse the fixture).
2. Run: `python -m generic_scraper describe --config <config>`
3. Expect exit code `0`.
4. Parse stdout as JSON. Assert:
   - `.engine == "<engine>"`
   - `.requested_engine == "<engine>"`
   - `.fallback_chain == ["<engine>"]` (no fallback occurred)
5. Run: `python -m generic_scraper fetch --config <config> --fixture fixtures/test_page.html --url https://example.com/test-page`
6. Expect exit code `0` and `.status == "ok"` — the scraper was "ready to
   fetch pages".

## QA-1.2 — Unknown engine is rejected here too

1. Config with `scraper_engine: bogus`.
2. Run `describe`. Expect non-zero exit and stderr starting with
   `UnsupportedScraperEngineError`. Stdout is empty.
