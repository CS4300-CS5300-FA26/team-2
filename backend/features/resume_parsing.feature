Feature: Resume parsing
  As a job seeker
  I want my resume turned into editable profile fields
  So that I can correct the information the system finds

  Scenario: Parse and edit an uploaded resume
    Given I am logged in and have uploaded a resume
    When the system parses my resume into profile fields
    And I correct one of the parsed fields
    Then my corrected resume fields are saved