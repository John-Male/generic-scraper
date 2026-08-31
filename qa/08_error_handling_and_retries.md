# QA — 08 Error handling, retries, and fallback behavior

Covers scenarios `error_handling_and_retries-1..3`.

## QA-8.1 — Transient errors are retried up to the configured attempt count

For each `attempts` in `3`, `5`:

1. Config with `scraper_engine: requests` and
   `retry: {attempts: <attempts>, backoff: exponential}`.
2. Force more failures than attempts:
   `python -m generic_scraper fetch --config <config> --url https://example.com/test-page --fixture fixtures/test_page.html --transient-errors <attempts + 1> --report-attempts`
3. Expect **non-zero** exit (all attempts exhausted). Assert stderr names a
   transient-fetch failure, and `--report-attempts` output shows exactly
   `<attempts>` attempts were made.
4. Re-run with `--transient-errors <attempts - 1>`. Expect exit `0`,
   `.status == "ok"`, and the attempt count equals `<attempts>` (failures +
   one success).
5. Backoff uses an injected clock: the run completes without real wall-clock
   delay.

## QA-8.2 — Engine start failure falls back to the configured secondary

For each `engine` in `selenium`, `playwright`:

1. Config with `scraper_engine: <engine>` and `secondary: requests`.
2. Run:
   `python -m generic_scraper describe --config <config> --engine-start-failure <engine>`
3. Expect exit `0`. Assert:
   - `.engine == "requests"`
   - `.fallback_chain == ["<engine>", "requests"]`
   - initialization succeeded (command exited `0`, stdout is a valid plan).

## QA-8.3 — Unknown engine fails with a descriptive named error

1. Use `fixtures/configs/unknown_engine.yaml` (`scraper_engine: unknown`).
2. Run: `python -m generic_scraper describe --config fixtures/configs/unknown_engine.yaml`
3. Expect non-zero exit. Assert stdout is empty and stderr's first token is
   `UnsupportedScraperEngineError`, and the message names the offending value
   `unknown`.
