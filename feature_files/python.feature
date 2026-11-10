@python
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


    Scenario: run in python the Kortex API example called device routine
        When running the python '100-Overview/01-devices_routing.py' Kortex API example
        Then the Kortex API example was run successfully
        Then the python Kortex API device routine output is valid


    Scenario: run in python the Kortex API example called protection zones configuration
        When running the python '100-Overview/02-protection_zones_configuration.py' Kortex API example
        Then the Kortex API example was run successfully
        Then the python Kortex API protection zones configuration output is valid


    Scenario: run in python the Kortex API example called move angular and cartesian
        When running the python '102-Movement_high_level/01-move_angular_and_cartesian.py' Kortex API example
        Then the Kortex API example was run successfully
        Then the python Kortex API move angular and cartesian output is valid


    Scenario: run in python the Kortex API example called sequence
        When running the python '102-Movement_high_level/02-sequence.py' Kortex API example
        Then the Kortex API example was run successfully
        Then the python Kortex API sequence output is valid


    Scenario: run in python the Kortex API example called twist command
        When running the python '102-Movement_high_level/03-twist_command.py' Kortex API example
        Then the Kortex API example was run successfully
        Then the python Kortex API twist command output is valid


    Scenario: run in python the Kortex API example called send joint speeds
        When running the python '102-Movement_high_level/04-send_joint_speeds.py' Kortex API example
        Then the Kortex API example was run successfully
        Then the python Kortex API send joint speeds output is valid


    Scenario: run in python the Kortex API example called UART bridge
        When running the python '103-Gen3_uart_bridge/01-uart_bridge.py' Kortex API example
        Then the Kortex API example was run successfully
        Then the python Kortex API UART bridge output is valid


    Scenario: run in python the Kortex API example called GPIO bridge
        When running the python '104-Gen3_gpio_bridge/01-gpio_bridge.py' Kortex API example
        Then the Kortex API example was run successfully
        Then the python Kortex API GPIO bridge output is valid


    Scenario: run in python the Kortex API example called I2C bridge
        When running the python '105-Gen3_i2c_bridge/01-i2c_bridge.py' Kortex API example
        Then the Kortex API example was run successfully
        Then the python Kortex API I2C bridge output is valid


    Scenario: run in python the Kortex API example called gripper command
        When running the python '106-Gripper_command/01-gripper_command.py' Kortex API example
        Then the Kortex API example was run successfully
        Then the python Kortex API gripper command output is valid


    Scenario: run in python the Kortex API example called gripper low level command
        When running the python '107-Gripper_low_level_command/01-gripper_low_level_command.py' Kortex API example and pressing ESC once 'Press ESC to quit' is displayed
        Then the Kortex API example was run successfully
        Then the python Kortex API gripper low level command output is valid


    Scenario: run in python the Kortex API example called torque control cyclic
        When running the python '108-Gen3_torque_control/01-torque_control_cyclic.py' Kortex API example
        Then the Kortex API example was run successfully
        Then the python Kortex API torque control cyclic output is valid


    Scenario: run in python the Kortex API example called Gen3 ethernet bridge
        When running the python '109-Gen3_ethernet_bridge/01-ethernet_bridge_configuration.py' Kortex API example
        Then the Kortex API example was run successfully
        Then the python Kortex API Gen3 ethernet bridge output is valid


    Scenario: run in python the Kortex API example called send angular waypoint trajectory
        When running the python '110-Waypoints/01-send_angular_wapoint_trajectory.py' Kortex API example with a timeout of 120 seconds
        Then the Kortex API example was run successfully
        Then the python Kortex API send angular waypoint trajectory output is valid