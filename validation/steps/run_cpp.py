"""Step definitions to run and check the C++ Kortex API examples."""

import re
import subprocess

from pytest_bdd import parsers, then, when

# Folder where CMake puts the compiled examples
# (one executable per example)
cpp_build_path = "../api_cpp/examples/build"
DEFAULT_TIMEOUT = 60  # seconds


def search_output(pattern: str, execution_context):
    """Search a regex pattern in the output of the executed example.

    When the pattern is not found, the raw output (and error output) is
    printed to help debugging. Pytest shows it in the report of the failed
    test, or on the console with the ``-s`` option.

    *Args*:
        - pattern (string): Regex pattern to find in the output.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status

    *Returns*:
        - The match object, or None if the pattern was not found.
    """
    match = re.search(pattern, str(execution_context["stdout"]))
    if match is None:
        print(
            "Output did not match the expected pattern. "
            f"Status: {execution_context.get('status')}"
        )
        print(f"stdout: {execution_context['stdout']!r}")
        if execution_context.get("stderr"):
            print(f"stderr: {execution_context['stderr']!r}")
    return match


def run_cpp_file(file_name: str, timeout: int, execution_context):
    """Run the prebuilt executable of the specified C++ example.

    The CMake build names each executable after its source path, with '/'
    replaced by '_' and without the extension (ex:
    '000-Getting_started/01-api_creation.cpp' becomes
    '000-Getting_started_01-api_creation').

    *Args*:
        - file_name (string): Path and file name of the C++ source file of
        the example.
        - timeout (int): Maximum execution time, in seconds.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    exe_name = file_name.removesuffix(".cpp").replace("/", "_")
    path = f"{cpp_build_path}/{exe_name}"
    try:
        result = subprocess.run([path], capture_output=True, timeout=timeout)
        execution_context["stdout"] = result.stdout
        execution_context["stderr"] = result.stderr
        execution_context["status"] = (
            "success" if result.returncode == 0 else "failed"
        )
    except subprocess.TimeoutExpired as e:
        execution_context["stdout"] = e.stdout or ""
        execution_context["stderr"] = e.stderr or ""
        execution_context["status"] = "timeout"
    except FileNotFoundError:
        execution_context["status"] = "File Not Found"


@when(parsers.parse("running the C++ '{file_name}' Kortex API example"))
def cpp_run(file_name: str, execution_context):
    """Run the prebuilt C++ example with the default timeout.

    *Args*:
        - file_name (string): Path and file name of the C++ source file of
        the example.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    run_cpp_file(file_name, DEFAULT_TIMEOUT, execution_context)


@when(
    parsers.parse(
        "running the C++ '{file_name}' Kortex API example "
        "with a timeout of {timeout:d} seconds"
    )
)
def cpp_run_with_timeout(file_name: str, timeout: int, execution_context):
    """Run the prebuilt C++ example with a timeout given by the scenario.

    *Args*:
        - file_name (string): Path and file name of the C++ source file of
        the example.
        - timeout (int): Maximum execution time, in seconds.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    run_cpp_file(file_name, timeout, execution_context)


@then("the C++ Kortex API creation output is valid")
def assert_output_of_api_creation(results_tracker, execution_context):
    """Assert the output of the API Creation example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    pattern = (
        r"Creating session for communication\\n"
        r"Session created\\n"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the C++ Kortex API protobuf object manipulation output is valid")
def assert_output_of_protobuf_object_manipulation(
    results_tracker, execution_context
):
    """Assert the output of the protobuf object manipulation example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    pattern = (
        r"(?:protobuf_object_manipulation +\\n)?"
        r"joint 3 = 45\\n"
        r"(?:\[45\] = \d+\\n)+"
        r"JSON String : \\n"
        r'\{"name":"Serialized/Deserialized action"\}\\n'
        r"Google Protocol Buffer message : \\n"
        r"Serialized/Deserialized action\\n"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the C++ Kortex API mechanism output is valid")
def assert_output_of_api_mechanism(results_tracker, execution_context):
    """Assert the output of the API mechanism example (list of arm actions).

    The list of actions is printed for each way of calling the API: blocking
    function, callback function (the callback prints its list twice), future
    function and call with router option.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """

    def action_block(identifier: int) -> str:
        """Return the regex of the block of the action with this identifier."""
        return (
            r"={44}\\n"
            r"Action name : \w+\\n"
            rf"Action identifier: {identifier}\\n"
            r"Action type: \w+\\n"
            r"Action permissions: \\n"
            r"(?:\\t| )+- \w+\\n"
            r"={44}\\n"
        )

    action_list = (
        r"List of all actions in the arm:\\n"
        + "".join(action_block(i) for i in range(1, 5))
    )
    pattern = (
        r"Creating session for communication\\n"
        r"Session created\\n"
        r"Blocking function results: \\n(?:\\n)*"
        rf"{action_list}"
        r"Callback function results: \\n(?:\\n)*"
        rf"(?:{action_list})+"
        r"Future function results: \\n(?:\\n)*"
        rf"{action_list}"
        r"Call with router option results: \\n(?:\\n)*"
        rf"{action_list}"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the C++ Kortex API error management output is valid")
def assert_output_of_api_error_management(results_tracker, execution_context):
    """Assert the output of the API error management.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    pattern = (
        r"Creating session for communication\\n"
        r"Session created\\n"
        r"KDetailedoption detected what:\s+Device error, "
        r"Error sub type=USERNAME_EMPTY => "
        r"<srv: \d+, fct: \d+, msgType: \d+>\\n"
        r"description: Empty username\\n"
        r"KError error_code: \d+\\n"
        r"KError sub_code: \d+\\n"
        r"KError sub_string: Empty username\\n"
        r"Error code string equivalent: ERROR_DEVICE\\n"
        r"Error sub-code string equivalent: USERNAME_EMPTY\\n"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the C++ Kortex API notification output is valid")
def assert_output_of_api_notification(results_tracker, execution_context):
    """Assert the output of the API notification example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    stars = r"\*{32}\\n"
    pattern = (
        r"Creating session for communication\\n"
        r"Session created\\n"
        r"Subscribing to ConfigurationChange notifications\\n"
        r"Creating user profile to trigger notification\\n"
        r"Callback triger\\n"
        rf"{stars}"
        r"\*\*  Callback function called  \*\*\\n"
        r'\{"event":"CONFIGURATION_CREATED",'
        r'"timestamp":\{"sec":\d+,"usec":\d+\},'
        r'"userHandle":\{"identifier":\d+\},'
        r'"userProfileHandle":\{"identifier":\d+\},'
        r'"connection":\{"userHandle":\{"identifier":\d+\},'
        r'"connectionInformation":"type=TCP;ip=(?:\d{1,3}\.){3}\d{1,3};'
        r'port=\d+","connectionIdentifier":\d+\}\}\\n'
        rf"{stars}"
        r"Unsubscribing from ConfigurationChange notifications\\n"
        r"Deleting previously created user profile\\n"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the C++ Kortex API devices routing output is valid")
def assert_output_of_api_devices_routing(results_tracker, execution_context):
    """Assert the output of the API devices routing example (device list).

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    text = r'"[^"\\]+"'
    device = (
        r"-----------------------------\\n"
        r"-- [A-Z_]+: id = \d+ --\\n"
        r"device_type: [A-Z_]+\\n"
        r"firmware_version: \d+\\n"
        r"bootloader_version: \d+\\n"
        rf"model_number: {text}\\n"
        rf"part_number: {text}\\n"
        rf"part_number_revision: {text}\\n"
        rf"serial_number: {text}\\n"
        # Each byte is printed in hex, padded with a space (ex: ' 0')
        r"MAC address: (?:[0-9a-f ]{2}:){5}[0-9a-f ]{2}\\n"
    )
    pattern = (
        r"Creating session for communication\\n"
        r"Session created\\n"
        rf"(?:{device})+"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then(
    "the C++ Kortex API protection zone configuration output is valid"
)
def assert_output_of_api_protection_zone_configuration(
    results_tracker, execution_context
):
    """Assert the output of the protection zone configuration example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    number = r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"
    event = (
        r"EVENT : ACTION_START\\n"
        r"(?:EVENT : ACTION_FEEDBACK\\n)*"
        r"EVENT : ACTION_END\\n"
    )
    safe_position = rf"Moving the arm to a safe position\\n{event}"
    # The zone name is followed by a space before " Origin", so the output
    # contains two spaces there for the zones created by the example
    zones = (
        r"PROTECTION ZONES : \\n"
        r"(?:Protection Zone : [\w ]+ "
        rf"Origin : \[ (?:{number} ){{3}}\] "
        rf"Dimensions : \[ (?:{number} )+\]\\n)+"
    )
    move_in_front = (
        r"Moving in front of protection zone\.\.\.\\n"
        r"Reaching cartesian pose\.\.\.\\n"
        r"Waiting\s+for movement to finish \.\.\.\\n"
        rf"{event}"
        r"Cartesian pose reached\\n"
    )

    def move_inside(state: str) -> str:
        return (
            rf"Moving inside {state} protection zone\.\.\.\\n"
            r"Moving towards the protection zone for \d+ seconds\.\.\.\\n"
            r"Going back to home position\.\.\.\\n"
            rf"{safe_position}"
        )

    pattern = (
        r"Creating session for communication\\n"
        r"Session created\\n"
        rf"{safe_position}{zones}"
        rf"{move_in_front}{move_inside('disabled')}"
        r"Creating and enabling protection zone\.\.\.\\n"
        rf"{zones}"
        rf"{move_in_front}{move_inside('enabled')}"
        rf"{zones}"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then(
    "the C++ Kortex API move angular and cartesian output is valid"
)
def assert_output_of_move_angular_and_cartesian(
    results_tracker, execution_context
):
    """Assert the output of the move angular and cartesian example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    event = r"[A-Z_]+"

    def movement(kind: str, label: str, value_name: str) -> str:
        return (
            rf"Starting {kind} action movement \.\.\.\\n"
            r"Executing action\\n"
            r"Waiting for movement to finish \.\.\.\\n"
            rf"{label} movement completed\\n"
            rf"{value_name} value : {event}\\n"
        )

    pattern = (
        r"Creating session for communication\\n"
        r"Session created\\n"
        r"Moving the arm to a safe position\\n"
        r"Move to Home completed\\n"
        rf"Promise value : {event}\\n"
        rf"{movement('Cartesian', 'Cartesian', 'Reference')}"
        rf"{movement('angular', 'Angular', 'Promise')}"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then(
    "the C++ Kortex API sequence output is valid"
)
def assert_output_of_sequence(
    results_tracker, execution_context
):
    """Assert the output of the sequence example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    event = r"[A-Z_]+"

    def movement(kind: str, label: str, value_name: str) -> str:
        return (
            rf"Starting {kind} action movement \.\.\.\\n"
            r"Executing action\\n"
            r"Waiting for movement to finish \.\.\.\\n"
            rf"{label} movement completed\\n"
            rf"{value_name} value : {event}\\n"
        )

    pattern = (
        r"Creating session for communication\\n"
        r"Session created\\n"
        r"Moving the arm to a safe position\\n"
        r"Creating Sequence\\n"
        r"Appending Actions to Sequence\\n"
        r"Creating Cartesian action\\n"
        r"Creating angular action\\n"
        r"Creating sequence on device and executing it\\n"
        r"Waiting for sequence to finish \.\.\.\\n"
        # The notification callbacks run in different threads, so the
        # "Sequence task N completed." and "Sequence completed." lines can come
        # in any order (even interleaved). Only check they were all printed
        # before the final promise value.
        r"(?=(?:(?!Promise value).)*Sequence task 0 completed\.)"
        r"(?=(?:(?!Promise value).)*1 completed\.)"
        r"(?=(?:(?!Promise value).)*Sequence completed\.)"
        r"(?:(?!Promise value).)*"
        r"Promise value : SEQUENCE_COMPLETED\\n"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the C++ Kortex API twist command output is valid")
def assert_output_of_twist_command(results_tracker, execution_context):
    """Assert the output of the twist command example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    pattern = (
        r"Creating session for communication\\n"
        r"Session created\\n"
        r"Moving the arm to a safe position\\n"
        r"Sending twist command for \d+ seconds\.\.\.\\n"
        r"Stopping robot \.\.\.\\n"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the C++ Kortex API send joint speeds output is valid")
def assert_output_of_send_joint_speeds(results_tracker, execution_context):
    """Assert the output of the send joint speeds example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    pattern = (
        r"Creating session for communication\\n"
        r"Session created\\n"
        r"Moving the arm to the start position\.\.\.\\n"
        r"Sending the angular velocities to the robot for \d+ seconds\.\.\.\\n"
        r"Stopping the robot\\n"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the C++ Kortex API send UART bridge output is valid")
def assert_output_of_uart_bridge(results_tracker, execution_context):
    """Assert the output of the UART bridge example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    pattern = (
        r"Interconnect ID found = 0x[0-9a-fA-F]+\\n"
        r"Bridge ID# \d+ created between Interconnect \(dev#\d+\) "
        r"port #\d+ and external port #\d+\\n"
        r"Waiting about \d+ seconds to receive data from UART\\n"
        r"Characters received : .*?"
        r"Test over!"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the C++ Kortex API send GPIO bridge output is valid")
def assert_output_of_gpio_bridge(results_tracker, execution_context):
    """Assert the output of the GPIO bridge example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    gpio_step = (
        r"GPIO pin GPIO_IDENTIFIER_1 will be put at value "
        r"GPIO_VALUE_(?:HIGH|LOW)\\n"
        r"GPIO pin GPIO_IDENTIFIER_2 will be put at value "
        r"GPIO_VALUE_(?:HIGH|LOW)\\n"
        r"Value read for pin #3 is : [01]\\n"
        r"Value read for pin #4 is : [01]\\n"
    )
    pattern = (
        r"Setting pin #1 as output\.\.\.\\n"
        r"Setting pin #2 as output\.\.\.\\n"
        r"Setting pin #3 as input pullup\.\.\.\\n"
        r"Setting pin #4 as input pullup\.\.\.\\n"
        r"GPIO bridge object initialized\\n"
        rf"(?:{gpio_step}){{4}}"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the C++ Kortex API send I2C bridge output is valid")
def assert_output_of_i2c_bridge(results_tracker, execution_context):
    """Assert the output of the I2C bridge example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    server_error = (
        r"Error: Server protocol error, Error sub type=SUB_ERROR_NONE => "
        r"<srv: \d+, fct: \d+, msgType: \d+>(?:\\n)+"
    )
    pattern = (
        r"I2C bridge object initialized\\n"
        r"Reading byte array from interconnect I2C bus\.\.\.\\n"
        rf"{server_error}"
        r"Sending byte array to interconnect I2C bus\.\.\.\\n"
        rf"{server_error}"
        r"Reading byte array from interconnect I2C bus\.\.\.\\n"
        rf"{server_error}"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the C++ Kortex API send called gripper command output is valid")
def assert_output_of_gripper_command(results_tracker, execution_context):
    """Assert the output of the gripper command example.

    The number of "Reported ..." lines depends on the gripper speed, so
    each of those blocks accepts one or more lines.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    number = r"\d+(?:\.\d+)?"
    pattern = (
        r"Performing gripper test in position\.\.\.\\n"
        r"Setting position to 0\\n"
        r"(?:Setting position to 0\.\d\\n){9}"
        r"Opening gripper using speed command\.\.\.\\n"
        rf"(?:Reported position : {number}\\n)+"
        r"Closing gripper using speed command\.\.\.\\n"
        rf"(?:Reported speed : {number}\\n)+"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then(
    "the C++ Kortex API send called gripper low level command output is valid"
)
def assert_output_of_gripper_low_level_command(
    results_tracker, execution_context
):
    """Assert the output of the gripper low level command example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    pattern = (
        r"Creating sessions for communication\\n"
        r"GripperLowLevel object initialized\\n"
        r"Going to position : 0\\n"
        r"(?:Going to position : \d+\\n){10}"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the C++ Kortex API send called torque control cyclic output is valid")
def assert_output_of_torque_control_cyclic(results_tracker, execution_context):
    """Assert the output of the torque control cyclic command example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    pattern = (
        r"Creating transport objects\\n"
        r"Creating transport real time objects\\n"
        r"Creating sessions for communication\\n"
        r"Sessions created\\n"
        r"Moving the arm to a safe position\\n"
        r"Move to Home completed\\n"
        r"Promise value : ACTION_END\\n"
        r"Initializing the arm for torque control example\\n"
        r"Running torque control example for \d+ seconds\\n"
        r"Torque control example completed\\n"
        r"Torque control example clean exit\\n"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the C++ Kortex API send called ethernet bridge configuration output is valid")
def assert_output_of_ethernet_bridge_configuration(results_tracker, execution_context):
    """Assert the output of the ethernet bridge example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    pattern = (
        r"Initizalizing the API\.\.\.\\n"
        r"Done initizalizing the API\.\\n"
        r"Configuring and enabling the Ethernet bridge\.\.\.\\n"
        r"Done configuring the Ethernet bridge\.\\n"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the C++ Kortex API send called send angular waypoint trajectory output is valid")
def assert_output_of_send_angular_waypoit_trajectory(results_tracker, execution_context):
    """Assert the output of the send angular waypoint trajectory example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    pattern = (
        r"Creating session for communication\\n"
        r"Session created\\n"
        r"Moving the arm to a safe position\\n"
        r"Move to Home completed\\n"
        r"Promise value : ACTION_END\\n"
        r"Moving the arm creating a trajectory of \d+ angular waypoints\\n"
        r"Angular waypoint trajectory completed\\n"
        r"Promise value : ACTION_END\\n"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then(
    "the C++ Kortex API send called send cartesian waypoint trajectory output "
    "is valid"
)
def assert_output_of_send_cartesian_waypoint_trajectory(
    results_tracker, execution_context
):
    """Assert the output of the send cartesian waypoint trajectory example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    pattern = (
        r"Creating session for communication\\n"
        r"Session created\\n"
        r"Moving the arm to a safe position\\n"
        r"Move to Home completed\\n"
        r"Promise value : ACTION_END\\n"
        r"Moving the arm creating a trajectory of \d+ cartesian waypoints\\n"
        r"cartesian waypoint trajectory completed\\n"
        r"Promise value : ACTION_END\\n"
        r"Optimized cartesian waypoint trajectory completed\\n"
        r"Promise value : ACTION_END\\n"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the C++ Kortex API send called compute kinematics output is valid")
def assert_output_of_compute_kinematics(results_tracker, execution_context):
    """Assert the output of the compute kinematics example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    number = r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"
    joint_angles = rf"(?:\d+ : {number}\\n){{7}}"
    pattern = (
        r"Creating session for communication\\n"
        r"Session created\\n"
        r"Getting Angles for every joint\.\.\.\\n"
        r"Joint ID : Joint Angle\\n"
        rf"{joint_angles}"
        r"\\n"
        r"Computing Foward Kinematics using joint angles\.\.\.\\n"
        r"Pose calculated : \\n"
        rf"Coordinate \(x, y, z\)  : \({number}, {number}, {number}\)\\n"
        r"Theta \(theta_x, theta_y, theta_z\)  : "
        rf"\({number}, {number}, {number}\)\\n"
        r"\\n"
        r"Computing Inverse Kinematics using joint angles and pose\.\.\.\\n"
        r"Joint ID : Joint Angle\\n"
        rf"{joint_angles}"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the C++ Kortex API send called actuator low level velocity control output is valid")
def assert_output_of_actuator_low_level_velocity_control(results_tracker, execution_context):
    """Assert the output of the actuator low level velocity control example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    pattern = (
        r"Creating sessions for communication\\n"
        r"Sessions created\\n"
        r"Moving the arm to a safe position\\n"
        r"EVENT : ACTION_START\\n"
        r"EVENT : ACTION_END\\n"
        r"Initializing the arm for velocity low-level control example\\n"
        r"Sending velocity command of \d+ deg/s to actuator \d+ "
        r"for \d+ seconds\\n"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )



@then(
    "the C++ Kortex API send called actuator low level pseudo velocity "
    "control output is valid"
)
def assert_output_of_actuator_low_level_pseudo_velocity_control(
    results_tracker, execution_context
):
    """Assert the output of the actuator low level pseudo velocity example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    pattern = (
        r"Creating sessions for communication\\n"
        r"Sessions created\\n"
        r"Moving the arm to a safe position\\n"
        # The action notification callback runs in another thread, so its
        # "EVENT : <name>" output can be mixed up with other events (ex:
        # "EVENT : EVENT : ACTION_STARTACTION_FEEDBACK"). Only check that the
        # start and end events were printed, in that order.
        r".*ACTION_START.*ACTION_END\\n"
        r"Initializing the arm for velocity low-level control example\\n"
        # Then, the feedback of the moving actuator is printed as one JSON
        # object followed by a blank line. Nothing else (ex: "Kortex error")
        # is accepted until the end of the output.
        r'(?:\{"commandId":\d+[^{}]*\}|\\n)+'
        r"'\Z"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )

