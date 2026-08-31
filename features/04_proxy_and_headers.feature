@swarm-forge @proxy
Feature: Proxy configuration and header pass key
  As a secure distributed scraper
  I want to configure proxy settings and pass key header data
  So that the Scraper can route requests through a proxy and include authentication headers

  Scenario: Initialize Scraper with proxy settings
    Given I have a ScraperType configuration with:
      | key            | value                 |
      | scraper_engine | requests              |
      | use_proxy      | true                  |
      | proxy_url      | http://proxy.example  |
      | proxy_port     | 8080                  |
    When I initialize the Scraper on a worker node
    Then the Scraper should configure the HTTP client to use the proxy "http://proxy.example:8080"

  Scenario: Include pass key header when provided
    Given I have a ScraperType configuration with:
      | key            | value               |
      | use_proxy      | true                |
      | proxy_pass_key | X-Proxy-Auth        |
      | proxy_pass_val | secret-token-123    |
    When I initialize the Scraper
    Then the Scraper should include header "X-Proxy-Auth: secret-token-123" on proxied requests
