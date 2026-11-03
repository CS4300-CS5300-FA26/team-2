Feature: Saved Jobs page
  As a job seeker
  I want a "Saved Jobs" page
  So that I can find all my bookmarked jobs in one place

  Scenario: I see all my bookmarked listings
    Given I have bookmarked one or more listings
    When I navigate to the Saved Jobs page
    Then I see all of my bookmarked listings in one place
