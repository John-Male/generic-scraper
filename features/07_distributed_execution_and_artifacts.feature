@swarm-forge @distributed @artifacts
Feature: Distributed execution, artifact upload, and node affinity
  As a Swarm Forge orchestrated job
  I want to run scraping tasks across multiple workers, collect artifacts, and control node affinity
  So that scraping jobs scale and results are preserved

  Scenario: Run scraping job across multiple workers
    Given I have a ScraperType configuration with "scraper_engine" set to "requests"
    And the job is configured to run with 3 parallel shards
    When the Swarm Forge orchestrator schedules the job
    Then the job should run on 3 distinct worker nodes
    And each worker should produce a parsed artifact

  Scenario: Upload artifacts to central storage
    Given a worker produced "parsed_result.json"
    When the worker finishes the shard
    Then the artifact "parsed_result.json" should be uploaded to the job artifact store

  Scenario: Respect node affinity and resource limits
    Given a ScraperType configuration with "browser_type" set to "chrome"
    And the job requests GPU false and memory 2GB
    When the orchestrator schedules the job
    Then the job should be placed on a node that satisfies the resource constraints
