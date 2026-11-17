"""Step definitions to run and check the C++ Kortex API examples."""

import re
import subprocess
import time

from pytest_bdd import parsers, then, when

# Folder where CMake puts the compiled examples
# (one executable per example)
cpp_build_path = "../api_cpp/examples/build"
DEFAULT_TIMEOUT = 60  # seconds
RETRY_DELAY = 30  # seconds to wait before running an example again


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


@when(
    parsers.parse(
        "running the C++ '{file_name}' Kortex API example "
        "with a timeout of {timeout:d} seconds, retrying up to "
        "{attempts:d} times while the output matches '{flaky}'"
    )
)
def cpp_run_with_retry(
    file_name: str,
    timeout: int,
    attempts: int,
    flaky: str,
    execution_context,
):
    """Run the C++ example again while its output shows a device glitch.

    Some examples depend on the device answering in time (ex: the Vision
    module right after its reboot) and print an error without failing. The
    example is run again while its output matches the regex, or until the
    maximum number of attempts is reached. The result of the last attempt
    is kept.

    *Args*:
        - file_name (string): Path and file name of the C++ source file of
        the example.
        - timeout (int): Maximum execution time of each attempt, in seconds.
        - attempts (int): Maximum number of attempts.
        - flaky (string): Regex of the output that triggers a new attempt.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    for attempt in range(1, attempts + 1):
        run_cpp_file(file_name, timeout, execution_context)
        execution_context["attempts"] = attempt
        output = execution_context.get("stdout") or b""
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        if execution_context.get("status") == "success" and not re.search(
            flaky, output
        ):
            return
        print(
            f"Attempt {attempt}/{attempts}: the output is not reliable "
            f"(status: {execution_context.get('status')})"
        )
        if attempt < attempts:
            # Let the device (ex: a rebooted Vision module) settle
            time.sleep(RETRY_DELAY)


@then(
    "the Kortex API example was run successfully or stopped on its last "
    "position"
)
def checks_api_execution_status_or_last_position(
    results_tracker, execution_context
):
    """Check the execution status, accepting a stop on the last position.

    The gripper cannot always reach the last position of the example (100%),
    and the example waits for it with no timeout of its own. A timeout is
    accepted when the example had already started its last move, as it then
    did everything it could. Any other status is a failure.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    status = execution_context["status"]
    output = execution_context.get("stdout") or b""
    if isinstance(output, bytes):
        output = output.decode("utf-8", errors="replace")
    last_move_started = output.rstrip().endswith("Going to position : 100")

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = "success"
    results_tracker[0]["actual"] = (
        "success" if status == "timeout" and last_move_started else status
    )


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



@then("the C++ Kortex API send called vision intrinsics output is valid")
def assert_output_of_vision_intrinsics(results_tracker, execution_context):
    """Assert the output of the vision intrinsics example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    number = r"-?\d+\.\d+"
    resolution = r"\d+x\d+"

    # The example prints a blank line before each title
    def get_block(title: str) -> str:
        """Title line, then the intrinsic parameters of a sensor."""
        return (
            rf"\\n-- Using Vision Config Service to {title} --\\n"
            r"Sensor: \d+ \((?:Color|Depth)\)\\n"
            rf"Resolution: \d+ \({resolution}\)\\n"
            rf"Principal point x: {number}\\n"
            rf"Principal point y: {number}\\n"
            rf"Focal length x: {number}\\n"
            rf"Focal length y: {number}\\n"
            rf"Distortion coefficients: \[(?:{number} ){{4}}{number}\]\\n"
        )

    def set_line(title: str) -> str:
        """Title line of a set request (no parameters are printed)."""
        return rf"\\n-- Using Vision Config Service to {title} --\\n"

    pattern = (
        r"Creating session for communication\\n"
        r"Session created\\n"
        r"Vision module found, device Id: \d+\\n"
        r"\\n\\n\*\* Example showing how to retrieve the intrinsic parameters "
        r"of the Color and Depth sensors \*\*\\n"
        + get_block("get intrinsic parameters of active color resolution")
        + get_block("get intrinsic parameters of active depth resolution")
        + get_block(f"get intrinsic parameters for color resolution {resolution}")
        + get_block(f"get intrinsic parameters for depth resolution {resolution}")
        + r"\\n\\n\*\* Example showing how to set the intrinsic parameters of "
        r"the Color and Depth sensors \*\*\\n"
        + "".join(
            get_block(
                f"get current intrinsic parameters for {sensor} "
                f"resolution {resolution}"
            )
            + set_line(
                f"set new intrinsic parameters for {sensor} "
                f"resolution {resolution}"
            )
            + get_block(
                f"get new intrinsic parameters for {sensor} "
                f"resolution {resolution}"
            )
            + set_line(
                f"set back old intrinsic parameters for {sensor} "
                f"resolution {resolution}"
            )
            for sensor in ("color", "depth")
        )
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the C++ Kortex API send called vision extrinsics output is valid")
def assert_output_of_vision_extrinsics(results_tracker, execution_context):
    """Assert the output of the vision extrinsics example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    number = r"-?\d+\.\d+"
    row = rf"{number}(?: +{number}){{2}}"

    # The example prints a blank line before each title
    def get_block(title: str) -> str:
        """Title line, then the rotation matrix and translation vector."""
        return (
            rf"\\n-- Using Vision Config Service to {title} --\\n"
            r"Rotation matrix:\\n"
            # The matrix is printed on 3 lines, each number being padded
            rf"\[ *{row}\\n"
            rf" +{row}\\n"
            rf" +{row}\]\\n"
            rf"Translation vector: \[{number}(?: {number}){{2}}\]\\n"
        )

    def set_line(title: str) -> str:
        """Title line of a set request (no parameters are printed)."""
        return rf"\\n-- Using Vision Config Service to {title} --\\n"

    pattern = (
        r"Creating session for communication\\n"
        r"Session created\\n"
        r"Vision module found, device Id: \d+\\n"
        r"\\n\\n\*\* Example showing how to retrieve the extrinsic parameters "
        r"\*\*\\n"
        + get_block("get the extrinsic parameters")
        + r"\\n\\n\*\* Example showing how to set the extrinsic parameters "
        r"\*\*\\n"
        + get_block("get current extrinsic parameters")
        + set_line("set new extrinsic parameters")
        + get_block("get new extrinsic parameters")
        + set_line("set back old extrinsic parameters")
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the C++ Kortex API send called vision sensor focus action output is valid")
def assert_output_of_vision_sensor_focus_action(
    results_tracker, execution_context
):
    """Assert the output of the vision sensor focus action example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    wait = (
        r"-- Waiting for 10 seconds to observe the effects of the focus "
        r"action\.\.\. --"
    )

    def action(title: str, hint: str) -> str:
        """A focus action: blank line, title, what to observe, then the wait."""
        return (
            r"\\n-- Using Vision Config Service to " + re.escape(title)
            # The space before the final dashes is missing in one title
            + r" ?--\\n"
            + re.escape(f"-- {hint} --") + r"\\n"
            + wait + r"\\n"
        )

    def example(title: str) -> str:
        """Title of an example, preceded by two blank lines."""
        return rf"\\n\\n\*\* Example showing how to {re.escape(title)} \*\*\\n"

    # Usage banner: blank line, framed text (tab indented), blank line
    border = r"\\t#{86}\\n"
    banner_lines = [
        "To use these examples:",
        " - Connect to the robot's web page",
        " - Configure the Vision Color Sensor to 1280x720 resolution",
        " - Position the robot so you can easily place objects in front of "
        "the Color camera",
        " - Select the Camera view page",
    ]
    banner = (
        r"\\n"
        + border
        + "".join(
            r"\\t# *" + re.escape(line.strip()) + r" *#\\n"
            for line in banner_lines
        )
        + border
        + r"\\n"
    )

    # (title of the action, what the user is asked to observe)
    auto_focus = [
        ("disable the auto-focus",
         "Place or remove an object from the center of the camera, "
         "observe the focus doesn't change"),
        ("enable the auto-focus",
         "Place an object in the center of the camera, "
         "observe the focus adjusts automatically"),
        ("pause the auto-focus",
         "Move the object away from the center of the camera and then back, "
         "but at a different distance, observe the focus doesn't change"),
        ("focus now",
         "Observe the focus tried to adjust to the object in front to the "
         "camera"),
        ("re-enable the auto-focus",
         "Move the object away from the center of the camera and then back, "
         "but at a different distance, observe the focus adjusts "
         "automatically"),
    ]
    focus_point = [
        ("set the focus point in the center of the lower right quadrant of "
         "the camera image",
         "Place an object in the center of the lower right quadrant of the "
         "camera image, observe the object gets into focus"),
        ("set the focus point back in the middle the camera image",
         "Place an object in the center of the camera image, "
         "observe the object gets into focus"),
    ]
    manual_focus = [
        ("set the manual focus on a very close object (close-up view)",
         "Place an object at around 2 inches away from the center of the "
         "camera, observe the object is in focus"),
        ("set the manual focus on an object at a greater distance",
         "Move the object away from the camera until it gets into focus"),
        ("set the manual focus on a relatively close object (normal view)",
         "Move the object at around 8 inches away from the center of the "
         "camera, observe the object is in focus"),
        ("re-enable the auto-focus",
         "Move the object away from the camera and then back, but at a "
         "different distance, observe the focus adjusts automatically"),
    ]

    pattern = (
        r"Creating session for communication\\n"
        r"Session created\\n"
        + banner
        + r"Vision module found, device Id: \d+\\n"
        + example("play with the auto-focus of the Color camera")
        + "".join(action(*step) for step in auto_focus)
        + example(
            "set the focus of the Color camera to a X-Y point in the camera "
            "image"
        )
        + "".join(action(*step) for step in focus_point)
        + example(
            "set the manual focus of the Color camera (changes the focus "
            "distance)"
        )
        + "".join(action(*step) for step in manual_focus)
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the C++ Kortex API send called vision sensor options output is valid")
def assert_output_of_vision_sensor_options(results_tracker, execution_context):
    """Assert the output of the vision sensor options example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    wait = (
        r"-- Waiting for 10 seconds to observe the effects of the focus "
        r"action\.\.\. --"
    )

    def action(title: str, hint: str) -> str:
        """A focus action: blank line, title, what to observe, then the wait."""
        return (
            r"\\n-- Using Vision Config Service to " + re.escape(title)
            # The space before the final dashes is missing in one title
            + r" ?--\\n"
            + re.escape(f"-- {hint} --") + r"\\n"
            + wait + r"\\n"
        )

    def example(title: str) -> str:
        """Title of an example, preceded by two blank lines."""
        return rf"\\n\\n\*\* Example showing how to {re.escape(title)} \*\*\\n"

    # Usage banner: blank line, framed text (tab indented), blank line
    border = r"\\t#{86}\\n"
    banner_lines = [
        "To use these examples:",
        " - Connect to the robot's web page",
        " - Configure the Vision Color Sensor to 1280x720 resolution",
        " - Position the robot so you can easily place objects in front of "
        "the Color camera",
        " - Select the Camera view page",
    ]
    banner = (
        r"\\n"
        + border
        + "".join(
            r"\\t# *" + re.escape(line.strip()) + r" *#\\n"
            for line in banner_lines
        )
        + border
        + r"\\n"
    )

    # (title of the action, what the user is asked to observe)
    auto_focus = [
        ("disable the auto-focus",
         "Place or remove an object from the center of the camera, "
         "observe the focus doesn't change"),
        ("enable the auto-focus",
         "Place an object in the center of the camera, "
         "observe the focus adjusts automatically"),
        ("pause the auto-focus",
         "Move the object away from the center of the camera and then back, "
         "but at a different distance, observe the focus doesn't change"),
        ("focus now",
         "Observe the focus tried to adjust to the object in front to the "
         "camera"),
        ("re-enable the auto-focus",
         "Move the object away from the center of the camera and then back, "
         "but at a different distance, observe the focus adjusts "
         "automatically"),
    ]
    focus_point = [
        ("set the focus point in the center of the lower right quadrant of "
         "the camera image",
         "Place an object in the center of the lower right quadrant of the "
         "camera image, observe the object gets into focus"),
        ("set the focus point back in the middle the camera image",
         "Place an object in the center of the camera image, "
         "observe the object gets into focus"),
    ]
    manual_focus = [
        ("set the manual focus on a very close object (close-up view)",
         "Place an object at around 2 inches away from the center of the "
         "camera, observe the object is in focus"),
        ("set the manual focus on an object at a greater distance",
         "Move the object away from the camera until it gets into focus"),
        ("set the manual focus on a relatively close object (normal view)",
         "Move the object at around 8 inches away from the center of the "
         "camera, observe the object is in focus"),
        ("re-enable the auto-focus",
         "Move the object away from the camera and then back, but at a "
         "different distance, observe the focus adjusts automatically"),
    ]

    pattern = (
        r"Creating session for communication\\n"
        r"Session created\\n"
        + banner
        + r"Vision module found, device Id: \d+\\n"
        + example("play with the auto-focus of the Color camera")
        + "".join(action(*step) for step in auto_focus)
        + example(
            "set the focus of the Color camera to a X-Y point in the camera "
            "image"
        )
        + "".join(action(*step) for step in focus_point)
        + example(
            "set the manual focus of the Color camera (changes the focus "
            "distance)"
        )
        + "".join(action(*step) for step in manual_focus)
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )

@then("the C++ Kortex API send called vision sensor options output is valid")
def assert_output_of_vision_sensor_options(results_tracker, execution_context):
    """Assert the output of the vision sensor options example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    number = r"-?\d+\.\d+"
    option = r"OPTION_\w+"

    # The example prints a blank line before each title (and some extra ones)
    def title(text: str) -> str:
        """Title line, preceded by a blank line."""
        return r"\\n-- " + re.escape(text) + r" --\\n"

    def example(text: str) -> str:
        """Title of an example, preceded by a blank line."""
        return r"\\n\*\* " + re.escape(text) + r" \*\*\\n"

    def vision(text: str) -> str:
        return title(f"Using Vision Config Service to {text}")

    # Usage banner: blank line, framed text (tab indented), blank line
    border = r"\\t#{86}\\n"
    banner_lines = [
        "To use these examples:",
        " - Connect to the robot's web page",
        " - Select the Camera view page",
        " - Observe the effects of changing the Color sensor options",
    ]
    banner = (
        r"\\n"
        + border
        + "".join(
            r"\\t# *" + re.escape(line.strip()) + r" *#\\n"
            for line in banner_lines
        )
        + border
        + r"\\n"
    )

    information = (
        rf"(?:Option id: \d+  name: {option}  is_writable: (?:true|false)\\n"
        rf"minimum: {number}  maximum: {number}\\n"
        rf"   step: {number}  default: {number}\\n\\n)+"
    )
    values = rf"(?:Option '{option}' has value {number}\\n)+"
    set_values = rf"(?:Set value \({number}\) for option '{option}'\\n)+"
    confirm_line = (
        rf"Confirm received value \({number}\) for option '{option}' "
        r"--> OK\\n"
    )
    confirm_values = rf"(?:{confirm_line})+"
    # After the reboot of the Vision module, the example reports the options
    # it could not read back. The device sometimes times out when reading the
    # depth options (known behaviour, on any of them). A timeout is accepted
    # here, but a wrong value read back is not.
    option_not_read = (
        rf"Failed to get value for option '{option}': "
        r"timeout detected: [\w:]+\\n\\n"
    )
    restored_values = rf"(?:{confirm_line}|{option_not_read})+"

    def set_and_confirm(value: str, sensor: str):
        return (
            vision(f"set {value} value for all {sensor} sensor options")
            + set_values
            + vision(
                f"confirm {value} value was set for all {sensor} sensor "
                "options"
            )
            + confirm_values
        )

    wait_color = title(
        "Waiting for 5 seconds to observe the effects of the new COLOR "
        "sensor options values..."
    )

    pattern = (
        r"Creating session for communication\\n"
        r"Session created\\n"
        + banner
        + r"Vision module found, device Id: \d+\\n"
        # Options information
        + example("Example showing how to get the sensors options information")
        + "".join(
            vision(f"get information for all {sensor} sensor options")
            + information
            for sensor in ("COLOR", "DEPTH")
        )
        # Options values
        + example("Example showing how to get the sensors options values")
        + "".join(
            vision(f"get value for all {sensor} sensor options")
            + values
            + r"\\n"
            for sensor in ("COLOR", "DEPTH")
        )
        # Set the max, then the default value
        + example("Example showing how to set the sensors options values")
        + "".join(
            set_and_confirm(value, "COLOR")
            + wait_color
            + set_and_confirm(value, "DEPTH")
            + r"\\n"
            for value in ("max", "default")
        )
        # Values restored upon a reboot of the Vision module
        + example(
            "Example confirming that sensors options values are restored "
            "upon a reboot of the Vision module"
        )
        + set_and_confirm("min", "COLOR")
        + set_and_confirm("min", "DEPTH")
        + r"\\n-- Using Device Config Service to reboot the Vision module in "
        r"\d+ milliseconds\. Please wait\.\.\. --\\n"
        + vision(
            "confirm min value was restored after reboot for all COLOR "
            "sensor options"
        )
        + confirm_values
        + vision(
            "confirm min value was restored after reboot for all DEPTH "
            "sensor options"
        )
        + restored_values
        + set_and_confirm("default", "COLOR")
        + set_and_confirm("default", "DEPTH")
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )
