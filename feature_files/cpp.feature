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


    Scenario: Test to run in Cpp the Kortex API called devices routing
        When running the C++ '100-Overview/01-devices_routing.cpp' Kortex API example
        Then the Kortex API example was run successfully
        Then the C++ Kortex API devices routing output is valid


    Scenario: Test to run in Cpp the Kortex API called protection zone configuration
        When running the C++ '100-Overview/02-protection_zones_configuration.cpp' Kortex API example
        Then the Kortex API example was run successfully
        Then the C++ Kortex API protection zone configuration output is valid


    Scenario: Test to run in Cpp the Kortex API called move angular and cartesian
        When running the C++ '102-High_level_movement/01-move_angular_and_cartesian.cpp' Kortex API example
        Then the Kortex API example was run successfully
        Then the C++ Kortex API move angular and cartesian output is valid


    Scenario: Test to run in Cpp the Kortex API called sequence
        When running the C++ '102-High_level_movement/02-sequence.cpp' Kortex API example
        Then the Kortex API example was run successfully
        Then the C++ Kortex API sequence output is valid


    Scenario: Test to run in Cpp the Kortex API called twist command
        When running the C++ '102-High_level_movement/03-twist_command.cpp' Kortex API example
        Then the Kortex API example was run successfully
        Then the C++ Kortex API twist command output is valid


    Scenario: Test to run in Cpp the Kortex API called send joint speeds
        When running the C++ '102-High_level_movement/04-send_joint_speeds.cpp' Kortex API example with a timeout of 30 seconds
        Then the Kortex API example was run successfully
        Then the C++ Kortex API send joint speeds output is valid