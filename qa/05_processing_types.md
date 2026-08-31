# QA — 05 Choose processing type for parsing responses

Covers scenario `processing_types-1`.

## QA-5.1 — Each processing type is selected

For each `processor` in `beautifulsoup`, `lxml`, `html.parser`, `regex`:

1. Config with `processing_type: <processor>`.
2. Run: `python -m generic_scraper describe --config <config>`
3. Expect exit `0`. Assert `.processor == "<processor>"`.

## QA-5.2 — Each processing type actually parses a page

For each `processor` as above:

1. Run:
   `python -m generic_scraper fetch --config <config> --fixture fixtures/test_page.html --url https://example.com/test-page`
2. Expect exit `0`. Assert `.processor == "<processor>"`, `.status == "ok"`,
   and `.title == "Test Page"` (every processor extracts the same title from
   the same fixture).
