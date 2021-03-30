Feature: Message sending

    As a user I should be able to get instruments metadata

    Scenario: As a logged in user I should be able to send a message to a person
        Given I am logged in
        When I send a message to "John Doe"
        Then The person "John Doe" should receive a message
