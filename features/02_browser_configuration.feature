@swarm-forge @browser
Feature: Configure browser type for browser-based scraping engines
  As a distributed test
  I want to set the browser type when using Playwright or Selenium
  So that the Scraper launches the correct browser on the worker node

  Scenario Outline: Set browser type for Playwright or Selenium
    Given I have a ScraperType configuration with "scraper_engine" set to "<engine>"
    And "browser_type" set to "<browser>"
    When I initialize the Scraper on a Swarm Forge worker
    Then the Scraper should launch "<browser>" for "<engine>"

    Examples:
      | engine     | browser |
      | playwright | chrome  |
      | playwright | firefox |
      | selenium   | chrome  |
      | selenium   | firefox |
