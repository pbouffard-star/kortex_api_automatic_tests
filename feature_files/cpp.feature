@cpp
Feature: c++ examples

    Scenario: Test to run in Cpp the Kortex API called API Creation
        When running the C++ '000-Getting_started/01-api_creation.cpp' Kortex API example
        Then the Kortex API example was run successfully
        Then the C++ Kortex API creation output is valid


    Scenario: Test to run in Cpp the Kortex API called protobuf object manipulation
        When running the C++ '000-Getting_started/02-protobuf_object_manipulation.cpp' Kortex API example
        Then the Kortex API example was run successfully
        Then the C++ Kortex API protobuf object manipulation output is valid


    Scenario: Test to run in Cpp the Kortex API called api mechanisme
        When running the C++ '000-Getting_started/03-api_mechanism.cpp' Kortex API example
        Then the Kortex API example was run successfully
        Then the C++ Kortex API mechanism output is valid


    Scenario: Test to run in Cpp the Kortex API called error management
        When running the C++ '000-Getting_started/04-error_management.cpp' Kortex API example
        Then the Kortex API example was run successfully
        Then the C++ Kortex API error management output is valid


    Scenario: Test to run in Cpp the Kortex API called notification
        When running the C++ '000-Getting_started/05-notification.cpp' Kortex API example with a timeout of 15 seconds
        Then the Kortex API example was run successfully
        Then the C++ Kortex API notification output is valid