 @swarm-forge @defaults
Feature: Default and secondary choices for ScraperType
  As a resilient scraper
  I want sensible defaults and fallback options
  So that the Scraper can operate even when some options are not provided or unavailable

  Scenario: Use default values when none provided
    Given I have an empty ScraperType configuration
    When I initialize the Scraper
    Then the Scraper should use "requests" as the default scraper engine
    And the Scraper should have no browser configured

  Scenario: Use secondary choice when primary unavailable
    Given I have a ScraperType configuration with "scraper_engine" set to "playwright"
    And Playwright is not available on the worker node
    When I initialize the Scraper
    Then the Scraper should fall back to "requests"
