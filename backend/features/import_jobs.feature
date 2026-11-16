Feature: Real job listings
  As a job seeker
  I want to see real job listings from companies
  So that I can find actual jobs to apply to

  Scenario: Imported jobs show up in the feed
    Given the job import has run
    When I open the job feed
    Then I see the real listings with their company, location, and apply link
