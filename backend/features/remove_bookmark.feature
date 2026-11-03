Feature: Remove a bookmark
  As a job seeker
  I want to remove a bookmark
  So that my saved jobs page only includes my wanted/interested jobs

  Scenario: I remove a job from my saved jobs
    Given a listing is in my saved jobs list
    When I remove the bookmark
    Then the listing no longer appears on my Saved Jobs page
