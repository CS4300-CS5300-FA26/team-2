Feature: Private note on a saved job
  As a job seeker
  I want to add a private note on a saved job
  So that I can remember why I chose to save it

  Scenario: I add a private note to a saved job
    Given I am viewing a saved job
    When I add a private note to it
    Then the note is saved and visible only to me when I return to that listing
