"""Command-line interface: ``describe``, ``fetch``, and ``run``.

This is the only user interface. Every command reads a YAML ``ScraperType`` with
``--config``, prints exactly one JSON object to stdout on success and exits 0,
and on a handled error prints nothing to stdout, writes a message beginning with
the error class name to stderr, and exits non-zero.

No command touches a network or a real browser. The engine platform is always
the in-process fake; QA affordance flags configure it.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence

from generic_scraper.cli.parser import build_parser
from generic_scraper.errors import ScraperError

__all__ = ["main"]


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = args.handler(args)
    except ScraperError as error:
        print(str(error), file=sys.stderr)
        return 1
    except (OSError, ValueError) as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        return 1
    json.dump(result, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
