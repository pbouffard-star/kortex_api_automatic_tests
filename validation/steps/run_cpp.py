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
        r"(?:Sequence task \d+ completed\.\\n)+"
        r"Sequence completed\.\\n"
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