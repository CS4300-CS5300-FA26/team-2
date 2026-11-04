Feature: Resume management
  As a job seeker
  I want to replace or delete an uploaded resume
  So that my saved resumes stay current

  Scenario: Replace an uploaded resume
    Given I am logged in and have uploaded a resume
    When I replace my resume with a new valid file
    Then the new file replaces my old resume

  Scenario: Delete an uploaded resume
    Given I am logged in and have uploaded a resume
    When I delete my uploaded resume
    Then the resume is removed from my account