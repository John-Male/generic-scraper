@swarm-forge @resilience
Feature: Error handling, retries, and fallback behavior
  As a robust scraper
  I want the Scraper to handle common errors, retry, and fallback gracefully
  So that scraping jobs are resilient in distributed environments

  # error_handling_and_retries-1: Retry on transient network error
  Scenario Outline: error_handling_and_retries-1
    Given I have a ScraperType configuration with "scraper_engine" set to "requests"
    And retry policy set to <attempts> attempts with exponential backoff
    When a transient network error occurs during fetch
    Then the Scraper should retry up to <attempts> times before failing

    Examples:
      | attempts |
      | 3        |
      | 5        |

  # error_handling_and_retries-2: Fall back to secondary engine on engine failure
  Scenario Outline: error_handling_and_retries-2
    Given I have a ScraperType configuration with "scraper_engine" set to "<engine>"
    And "secondary" set to "requests"
    And "<engine>" fails to start on the worker
    When I initialize the Scraper
    Then the Scraper should attempt to use "requests" as the secondary engine
    And the initialization should succeed

    Examples:
      | engine     |
      | selenium   |
      | playwright |

  # error_handling_and_retries-3: Fail with descriptive error when no engine available
  Scenario Outline: error_handling_and_retries-3
    Given I have a ScraperType configuration with "scraper_engine" set to "<engine>"
    When I initialize the Scraper
    Then the Scraper initialization should fail with "<error>"

    Examples:
      | engine  | error                         |
      | unknown | UnsupportedScraperEngineError |
