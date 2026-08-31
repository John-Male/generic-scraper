"""Mutation-hardening tests.

These exist to kill specific mutants that the unit and acceptance suites leave
alive. They assert behaviour the other suites take for granted: value-object
immutability, error messages that name what was tried, exact default values,
and parser title/text extraction under awkward markup.

Run on their own with ``pytest -m hardening``.
"""
