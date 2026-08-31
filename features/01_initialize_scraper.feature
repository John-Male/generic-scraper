@swarm-forge @init
Feature: Initialize Scraper with chosen scraping engine
  As a test runner using Swarm Forge
  I want to initialize the Scraper with a chosen engine
  So that the scraper uses the correct technique for fetching pages

  Background:
    Given default scraper configuration exists

  Scenario Outline: Initialize Scraper with different engines
    Given I have a ScraperType configuration with "scraper_engine" set to "<engine>"
    When I initialize the Scraper
    Then the Scraper should use the "<engine>" engine
    And the Scraper should be ready to fetch pages

    Examples:
      | engine     |
      | requests   |
      | playwright |
      | selenium   |
