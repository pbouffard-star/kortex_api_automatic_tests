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
        Then the 'jcash' user profile is removed from the arm
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


    Scenario: Test to run in Cpp the Kortex API called send UART bridge
        When running the C++ '103-Gen3_uart_bridge/01-uart_bridge.cpp' Kortex API example
        Then the Kortex API example was run successfully
        Then the C++ Kortex API send UART bridge output is valid


    Scenario: Test to run in Cpp the Kortex API called GPIO bridge
        When running the C++ '104-Gen3_gpio_bridge/01-gpio_bridge.cpp' Kortex API example
        Then the Kortex API example was run successfully
        Then the C++ Kortex API send GPIO bridge output is valid


    Scenario: Test to run in Cpp the Kortex API called I2C bridge
        When running the C++ '105-Gen3_i2c_bridge/01-i2c_bridge.cpp' Kortex API example
        Then the Kortex API example was run successfully
        Then the C++ Kortex API send I2C bridge output is valid


    Scenario: Test to run in Cpp the Kortex API called gripper command
        When running the C++ '106-Gripper_command/01-gripper_command.cpp' Kortex API example
        Then the Kortex API example was run successfully
        Then the C++ Kortex API send called gripper command output is valid


    Scenario: Test to run in Cpp the Kortex API called gripper low level command
        When running the C++ '107-Gripper_low_level_command/01-gripper_low_level_command.cpp' Kortex API example
        Then the Kortex API example was run successfully
        Then the C++ Kortex API send called gripper low level command output is valid


    Scenario: Test to run in Cpp the Kortex API called torque control cyclic
        When running the C++ '108-Gen3_torque_control/01-torque_control_cyclic.cpp' Kortex API example
        Then the Kortex API example was run successfully
        Then the C++ Kortex API send called torque control cyclic output is valid


    Scenario: Test to run in Cpp the Kortex API ethernet bridge configuration
        When running the C++ '109-Gen3_ethernet_bridge/01-ethernet_bridge_configuration.cpp' Kortex API example
        Then the Kortex API example was run successfully
        Then the C++ Kortex API send called ethernet bridge configuration output is valid


    Scenario: Test to run in Cpp the Kortex API send angular waypoint trajectory
        When running the C++ '110-Waypoints/01-send_angular_wapoint_trajectory.cpp' Kortex API example with a timeout of 120 seconds
        Then the Kortex API example was run successfully
        Then the C++ Kortex API send called send angular waypoint trajectory output is valid


    Scenario: Test to run in Cpp the Kortex API send cartesian waypoint trajectory
        When running the C++ '110-Waypoints/02-send_cartesian_waypoint_trajectory.cpp' Kortex API example with a timeout of 180 seconds
        Then the Kortex API example was run successfully
        Then the C++ Kortex API send called send cartesian waypoint trajectory output is valid


    Scenario: Test to run in Cpp the Kortex API compute kinematics
        When running the C++ '111-Kinematics/01-compute-kinematics.cpp' Kortex API example
        Then the Kortex API example was run successfully
        Then the C++ Kortex API send called compute kinematics output is valid


    Scenario: Test to run in Cpp the Kortex API actuator low level velocity control
        When running the C++ '200-Actuator_low_level_control/01-actuator_low_level_velocity_control.cpp' Kortex API example
        Then the Kortex API example was run successfully
        Then the C++ Kortex API send called actuator low level velocity control output is valid


    Scenario: Test to run in Cpp the Kortex API actuator low level pseudo velocity control
        When running the C++ '200-Actuator_low_level_control/02-actuator_low_level_pseudo_velocity_control.cpp' Kortex API example
        Then the Kortex API example was run successfully
        Then the C++ Kortex API send called actuator low level pseudo velocity control output is valid


    Scenario: Test to run in Cpp the Kortex API vision intrinsics
        When running the C++ '500-Gen3_vision_configuration/01_vision_intrinsics.cpp' Kortex API example
        Then the Kortex API example was run successfully
        Then the C++ Kortex API send called vision intrinsics output is valid


    Scenario: Test to run in Cpp the Kortex API vision extrinsics
        When running the C++ '500-Gen3_vision_configuration/02_vision_extrinsics.cpp' Kortex API example
        Then the Kortex API example was run successfully
        Then the C++ Kortex API send called vision extrinsics output is valid


    Scenario: Test to run in Cpp the Kortex API vision sensor focus action
        When running the C++ '500-Gen3_vision_configuration/03_vision_sensor_focus_action.cpp' Kortex API example with a timeout of 180 seconds
        Then the Kortex API example was run successfully
        Then the C++ Kortex API send called vision sensor focus action output is valid


    Scenario: Test to run in Cpp the Kortex API vision sensor options
        When running the C++ '500-Gen3_vision_configuration/04_vision_sensor_options.cpp' Kortex API example with a timeout of 120 seconds, retrying up to 4 times while the output matches 'Failed to set|FAILED'
        Then the Kortex API example was run successfully
        Then the C++ Kortex API send called vision sensor options output is valid