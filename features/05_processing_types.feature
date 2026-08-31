@swarm-forge @parser
Feature: Choose processing type for parsing responses
  As a developer running tests in Swarm Forge
  I want to select a processing type (parser) for the Scraper
  So that the Scraper can parse HTML using different libraries

  # processing_types-1: Initialize Scraper with different processing types
  Scenario Outline: processing_types-1
    Given I have a ScraperType configuration with "processing_type" set to "<processor>"
    When I initialize the Scraper
    Then the Scraper should use "<processor>" to parse HTML responses

    Examples:
      | processor     |
      | beautifulsoup |
      | lxml          |
      | html.parser   |
      | regex         |
