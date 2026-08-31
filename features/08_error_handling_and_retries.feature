@swarm-forge @resilience
Feature: Error handling, retries, and fallback behavior
  As a robust scraper
  I want the Scraper to handle common errors, retry, and fallback gracefully
  So that scraping jobs are resilient in distributed environments

  Scenario: Retry on transient network error
    Given I have a ScraperType configuration with "scraper_engine" set to "requests"
    And retry policy set to 3 attempts with exponential backoff
    When a transient network error occurs during fetch
    Then the Scraper should retry up to 3 times before failing

  Scenario: Fallback to secondary engine on engine failure
    Given I have a ScraperType configuration with:
      | key            | value    |
      | scraper_engine | selenium |
      | secondary      | requests |
    And Selenium fails to start on the worker
    When I initialize the Scraper
    Then the Scraper should attempt to use "requests" as the secondary engine
    And the initialization should succeed

  Scenario: Fail with descriptive error when no engine available
    Given I have a ScraperType configuration with:
      | key            | value   |
      | scraper_engine | unknown |
    When I initialize the Scraper
    Then the Scraper initialization should fail with "UnsupportedScraperEngineError"
