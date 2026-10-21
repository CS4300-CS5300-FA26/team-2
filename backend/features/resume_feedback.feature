Feature: AI resume feedback
  As a job seeker
  I want AI feedback on my uploaded resume
  So that I can see what needs improvement

  Scenario: Request feedback for an uploaded resume
    Given I am logged in and have uploaded a resume
    When I request AI feedback for my resume
    Then I receive suggestions about what could be improved