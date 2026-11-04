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
        Then the python Kortex protobuf object manipulation is valid