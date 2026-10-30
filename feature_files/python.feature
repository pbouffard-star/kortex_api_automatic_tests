@python
Feature: python examples

    @weekly
    Scenario: Test to run in python the Kortex API called API Creation
        When running the python '000-Getting_Started/01-api_creation.py' Kortex API example
        Then the Kortex API example was run successfully