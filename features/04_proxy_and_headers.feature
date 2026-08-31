@swarm-forge @proxy
Feature: Proxy configuration and header pass key
  As a secure distributed scraper
  I want to configure proxy settings and pass key header data
  So that the Scraper can route requests through a proxy and include authentication headers

  Background:
    Given I have a ScraperType configuration with "use_proxy" set to "true"

  # proxy_and_headers-1: Initialize Scraper with proxy settings
  Scenario Outline: proxy_and_headers-1
    Given "scraper_engine" set to "requests"
    And "proxy_url" set to "<proxy_url>"
    And "proxy_port" set to "<proxy_port>"
    When I initialize the Scraper on a worker node
    Then the Scraper should configure the HTTP client to use the proxy "<proxy_url>:<proxy_port>"

    Examples:
      | proxy_url             | proxy_port |
      | http://proxy.example  | 8080       |
      | http://proxy.internal | 3128       |

  # proxy_and_headers-2: Include pass key header when provided
  Scenario Outline: proxy_and_headers-2
    Given "proxy_pass_key" set to "<pass_key>"
    And "proxy_pass_val" set to "<pass_val>"
    When I initialize the Scraper
    Then the Scraper should include header "<pass_key>: <pass_val>" on proxied requests

    Examples:
      | pass_key     | pass_val        |
      | X-Proxy-Auth | dummy-token-abc |
      | X-Auth-Token | dummy-token-xyz |
