Feature: Default resume
  As a job seeker
  I want to choose one uploaded resume as my default
  So that I know which resume will be used first

  Scenario: Choose a different resume as the default
    Given I have two uploaded resumes and the first is my default
    When I choose my second resume as the default
    Then only my second resume is marked as the default