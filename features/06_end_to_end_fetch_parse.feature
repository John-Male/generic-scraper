@swarm-forge @e2e
Feature: End-to-end fetch and parse using configured options
  As a distributed test
  I want the Scraper to fetch a page and parse it using the configured engine and processor
  So that I can verify the full pipeline works across Swarm Forge workers

  Background:
    Given a test URL "https://example.com/test-page"

  # end_to_end_fetch_parse-1: Fetch and parse using engine and processor
  Scenario Outline: end_to_end_fetch_parse-1
    Given I have a ScraperType configuration with "scraper_engine" set to "<engine>"
    And "processing_type" set to "<processor>"
    When I initialize the Scraper on a worker node
    And I fetch the test URL
    Then the Scraper should return a parsed document using "<processor>"
    And the parsed document should contain the page title

    Examples:
      | engine     | processor     |
      | requests   | beautifulsoup |
      | requests   | lxml          |
      | selenium   | beautifulsoup |
      | playwright | html.parser   |
