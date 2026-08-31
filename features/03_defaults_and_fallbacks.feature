@swarm-forge @defaults
Feature: Default and secondary choices for ScraperType
  As a resilient scraper
  I want sensible defaults and fallback options
  So that the Scraper can operate even when some options are not provided or unavailable

  # defaults_and_fallbacks-1: Use default values when none provided
  Scenario: defaults_and_fallbacks-1
    Given I have an empty ScraperType configuration
    When I initialize the Scraper
    Then the Scraper should use "requests" as the default scraper engine
    And the Scraper should have no browser configured

  # defaults_and_fallbacks-2: Fall back when primary engine unavailable and no secondary configured
  Scenario Outline: defaults_and_fallbacks-2
    Given I have a ScraperType configuration with "scraper_engine" set to "<engine>"
    And "<engine>" is not available on the worker node
    When I initialize the Scraper
    Then the Scraper should fall back to "requests"

    Examples:
      | engine     |
      | playwright |
      | selenium   |
