@swarm-forge @e2e
Feature: End-to-end fetch and parse using configured options
  As a distributed test
  I want the Scraper to fetch a page and parse it using the configured engine and processor
  So that I can verify the full pipeline works across Swarm Forge workers

  Background:
    Given a test URL "https://example.com/test-page"

  Scenario Outline: Fetch and parse using engine and processor
    Given I have a ScraperType configuration with:
      | key             | value        |
      | scraper_engine  | <engine>     |
      | processing_type | <processor>  |
    When I initialize the Scraper on a worker node
    And I fetch "https://example.com/test-page"
    Then the Scraper should return a parsed document using "<processor>"
    And the parsed document should contain the page title

    Examples:
      | engine     | processor     |
      | requests   | beautifulsoup |
      | requests   | lxml          |
      | selenium   | beautifulsoup |
      | playwright | html.parser   |
