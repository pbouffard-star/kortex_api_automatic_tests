@cpp
Feature: c++ examples

    @weekly
    Scenario: Test to run in Cpp the Kortex API called API Creation
        When running the c++ '000-Getting_started/01-api_creation.cpp' Kortex API example
        Then the Kortex API example was run successfully
        Then the C++ Kortex API creation returns:

            | session               | created                 |