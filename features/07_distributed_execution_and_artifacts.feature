@swarm-forge @distributed @artifacts
Feature: Distributed execution, artifact upload, and node affinity
  As a Swarm Forge orchestrated job
  I want to run scraping tasks across multiple workers, collect artifacts, and control node affinity
  So that scraping jobs scale and results are preserved

  # distributed_execution_and_artifacts-1: Run scraping job across multiple workers
  Scenario Outline: distributed_execution_and_artifacts-1
    Given I have a ScraperType configuration with "scraper_engine" set to "requests"
    And the job is configured to run with <shards> parallel shards
    When the orchestrator schedules the job
    Then the job should run on <shards> distinct worker nodes
    And each worker should produce a parsed artifact

    Examples:
      | shards |
      | 3      |
      | 5      |

  # distributed_execution_and_artifacts-2: Upload artifacts to central storage
  Scenario Outline: distributed_execution_and_artifacts-2
    Given a worker produced "<artifact>"
    When the worker finishes the shard
    Then the artifact "<artifact>" should be uploaded to the job artifact store

    Examples:
      | artifact           |
      | parsed_result.json |

  # distributed_execution_and_artifacts-3: Respect node affinity and resource limits
  Scenario: distributed_execution_and_artifacts-3
    Given a ScraperType configuration with "browser_type" set to "chrome"
    And the job requests GPU false and memory 2GB
    When the orchestrator schedules the job
    Then the job should be placed on a node that satisfies the resource constraints
