"""Error types raised by the scraper.

Every error carries a human-readable message that names what was tried, so a
distributed job log makes the failure obvious without a stack trace.
"""

from __future__ import annotations


class ScraperError(Exception):
    """Base class for every error this package raises deliberately."""


class UnsupportedScraperEngineError(ScraperError):
    """The configured ``scraper_engine`` is not a name this package knows."""


class UnsupportedProcessingTypeError(ScraperError):
    """The configured ``processing_type`` is not a name this package knows."""


class NoEngineAvailableError(ScraperError):
    """Every engine in the fallback chain was tried and none could start."""


class TransientFetchError(ScraperError):
    """A fetch attempt failed in a way that is worth retrying."""


class FetchError(ScraperError):
    """A fetch failed permanently, or every retry was exhausted."""
