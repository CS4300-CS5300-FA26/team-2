Feature: Track my applications on saved jobs
  As a job seeker
  I want to set a status on my saved jobs and filter by it
  So that I can keep track of my applications and see which need follow-up

  Scenario: I set a status on a saved job (US4.5)
    Given I am viewing a saved job
    When I set its status to "interviewing"
    Then the status "interviewing" is saved and shown on my Saved Jobs page

  Scenario: I filter my saved jobs by status (US4.6)
    Given I have saved jobs with different statuses
    When I filter my Saved Jobs page by "applied"
    Then only the jobs with the status "applied" are shown
