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
