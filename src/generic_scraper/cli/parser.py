"""argparse construction for the scraper CLI.

Kept separate from the command handlers so the flag surface can be read in one
place and the handlers stay free of argparse boilerplate.
"""

from __future__ import annotations

import argparse

from generic_scraper.cli.commands import describe, fetch, run

DEFAULT_URL = "https://example.com/test-page"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="generic-scraper")
    subs = parser.add_subparsers(dest="command", required=True)

    describe_cmd = subs.add_parser("describe", help="print the resolved scraper plan")
    _add_config_flag(describe_cmd)
    _add_engine_flags(describe_cmd)
    describe_cmd.set_defaults(handler=describe, fixture=None)

    fetch_cmd = subs.add_parser("fetch", help="fetch one URL and parse it")
    _add_config_flag(fetch_cmd)
    _add_engine_flags(fetch_cmd)
    fetch_cmd.add_argument("--url", default=DEFAULT_URL)
    fetch_cmd.add_argument(
        "--fixture", help="read this saved page instead of the network"
    )
    fetch_cmd.add_argument("--report-attempts", action="store_true")
    fetch_cmd.add_argument("--print-request-headers", action="store_true")
    fetch_cmd.set_defaults(handler=fetch)

    run_cmd = subs.add_parser(
        "run", help="schedule a sharded job on the fake orchestrator"
    )
    _add_config_flag(run_cmd)
    run_cmd.add_argument("--url", default=DEFAULT_URL)
    run_cmd.add_argument("--fixture")
    run_cmd.add_argument("--shards", type=int, default=1)
    run_cmd.add_argument("--artifact-dir")
    run_cmd.add_argument("--artifact-store")
    run_cmd.add_argument("--orchestrator", choices=["fake"], default="fake")
    run_cmd.add_argument("--job-resources", default="")
    run_cmd.add_argument("--node-capacity", default="")
    run_cmd.set_defaults(handler=run)

    return parser


def _add_config_flag(sub: argparse.ArgumentParser) -> None:
    sub.add_argument("--config", help="path to a YAML ScraperType file")


def _add_engine_flags(sub: argparse.ArgumentParser) -> None:
    sub.add_argument("--engine-unavailable", action="append", default=[])
    sub.add_argument("--engine-start-failure", action="append", default=[])
    sub.add_argument("--transient-errors", type=int, default=0)
