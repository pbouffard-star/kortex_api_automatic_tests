@python @weekly
Feature: python examples

    Scenario: run in python the Kortex API example called API Creation
        When running the python '000-Getting_Started/01-api_creation.py' Kortex API example
        Then the Kortex API example was run successfully
        Then the python Kortex API creation returns:

            | session               | created                 |
            | device type           | BASE                    |
            | active state          | ARMSTATE_SERVOING_READY |


    Scenario: run in python the Kortex API example called protobuf object manipulation
        When running the python '000-Getting_Started/02-protobuf_object_manipulation.py' Kortex API example
        Then the Kortex API example was run successfully
        Then the python Kortex protobuf object manipulation output is valid

    Scenario: run in python the Kortex API example called api mechanism
        When running the python '000-Getting_Started/03-api_mechanism.py' Kortex API example
        Then the Kortex API example was run successfully
        Then the python Kortex api mechanism output is valid

    Scenario: run in python the Kortex API example called error management
        When running the python '000-Getting_Started/04-error_management.py' Kortex API example
        Then the Kortex API example was run successfully
        Then the python Kortex API error management returns:
        
            | Error_code          | 3              |
            | Sub_error_code      | 105            |
            | Server error name   | ERROR_DEVICE   |
            | sub name            | USERNAME_EMPTY |


    Scenario: run in python the Kortex API example called notification
        When running the python '000-Getting_Started/05-notification.py' Kortex API example
        Then the Kortex API example was run successfully
        Then the python Kortex API notification output is valid