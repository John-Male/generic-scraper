# QA — 03 Default and secondary choices for ScraperType

Covers scenarios `defaults_and_fallbacks-1`, `defaults_and_fallbacks-2`.

## QA-3.1 — Empty config uses documented defaults

1. Use `fixtures/configs/empty.yaml` (`{}`).
2. Run: `python -m generic_scraper describe --config fixtures/configs/empty.yaml`
3. Expect exit `0`. Assert on stdout JSON:
   - `.engine == "requests"`
   - `.browser == null`

## QA-3.2 — Unavailable primary engine falls back to requests

For each `engine` in `playwright`, `selenium`:

1. Config with `scraper_engine: <engine>` and no `secondary`.
2. Run:
   `python -m generic_scraper describe --config <config> --engine-unavailable <engine>`
3. Expect exit `0`. Assert:
   - `.requested_engine == "<engine>"`
   - `.engine == "requests"`
   - `.fallback_chain == ["<engine>", "requests"]`
