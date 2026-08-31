# generic-scraper

A configuration-driven web scraper. Describe a site in a spec file; get
structured records out. Built by a SwarmForge six-pack running on Claude Code.

    python -m venv .venv && source .venv/bin/activate
    pip install requests beautifulsoup4 lxml PyYAML pytest pytest-bdd ruff mypy
    pytest

Behavior lives in `features/*.feature`; step definitions in
`tests/acceptance/steps/`.
