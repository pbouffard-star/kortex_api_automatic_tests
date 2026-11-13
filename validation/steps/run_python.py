"""Step definitions to run and check the python Kortex API examples."""

import os
import pty
import re
import select
import subprocess
import time

from pytest_bdd import parsers, then, when

python_ex_file_path = "../api_python/examples"
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


def run_python_file(file_name: str, timeout: int, execution_context):
    """Run the specified python file and store the result.

    *Args*:
        - file_name (string): Path and file name of the python file.
        - timeout (int): Maximum execution time, in seconds.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    path = f"{python_ex_file_path}/{file_name}"
    try:
        result = subprocess.run(
            ["python3.9", "-u", path], capture_output=True, timeout=timeout
        )
        execution_context["stdout"] = result.stdout
        execution_context["stderr"] = result.stderr
        execution_context["status"] = (
            "success" if result.returncode == 0 else "failed"
        )
    except subprocess.TimeoutExpired as e:
        execution_context["stdout"] = e.stdout or ""
        execution_context["stderr"] = e.stderr or ""
        execution_context["status"] = "timeout"
    except subprocess.CalledProcessError as e:
        execution_context["stdout"] = e.stdout
        execution_context["stderr"] = e.stderr
        execution_context["status"] = "failed"
    except FileNotFoundError:
        execution_context["status"] = "File Not Found"


@when(parsers.parse("running the python '{file_name}' Kortex API example"))
def python_run(file_name: str, execution_context):
    """Run the specified python file with the default timeout.

    *Args*:
        - file_name (string): Path and file name of the python file.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    run_python_file(file_name, DEFAULT_TIMEOUT, execution_context)


@when(
    parsers.parse(
        "running the python '{file_name}' Kortex API example "
        "with a timeout of {timeout:d} seconds"
    )
)
def python_run_with_timeout(
    file_name: str, timeout: int, execution_context
):
    """Run the specified python file with a timeout given by the scenario.

    *Args*:
        - file_name (string): Path and file name of the python file.
        - timeout (int): Maximum execution time, in seconds.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    run_python_file(file_name, timeout, execution_context)


@when(
    parsers.parse(
        "running the python '{file_name}' Kortex API example "
        "with a timeout of {timeout:d} seconds, retrying up to "
        "{attempts:d} times unless the output ends with '{ending}'"
    )
)
def python_run_with_retry(
    file_name: str,
    timeout: int,
    attempts: int,
    ending: str,
    execution_context,
):
    """Run the python file again if its output does not end as expected.

    Some examples are not reliable (for example because of a race condition
    in the example itself). The file is run until the output ends with the
    expected text, or until the maximum number of attempts is reached. The
    result of the last attempt is kept.

    *Args*:
        - file_name (string): Path and file name of the python file.
        - timeout (int): Maximum execution time of each attempt, in seconds.
        - attempts (int): Maximum number of attempts.
        - ending (string): Text the output must end with to be accepted.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    for attempt in range(1, attempts + 1):
        run_python_file(file_name, timeout, execution_context)
        execution_context["attempts"] = attempt
        output = execution_context.get("stdout") or b""
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        if output.rstrip().endswith(ending):
            return
        print(
            f"Attempt {attempt}/{attempts}: the output does not end with "
            f"{ending!r} (status: {execution_context.get('status')})"
        )


ESC_KEY = b"\x1b"


def run_python_with_key_presses(
    file_name: str, key_presses: list, execution_context
):
    """Run the python file in a pseudo terminal and send keys on prompts.

    Some examples wait for a key press on the keyboard (``termios``), which
    needs a real terminal as standard input. The file is run with a
    pseudo terminal as stdin. Each key is sent, in order, once its prompt is
    displayed in the output (after the previous prompt).

    *Args*:
        - file_name (string): Path and file name of the python file.
        - key_presses (list): List of (prompt, key) tuples. The key (bytes)
        is sent once the prompt (string) is displayed in the output.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    path = f"{python_ex_file_path}/{file_name}"
    timeout = 30
    master_fd, slave_fd = pty.openpty()
    process = subprocess.Popen(
        ["python3.9", "-u", path],
        stdin=slave_fd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    os.close(slave_fd)
    stdout = b""
    status = "timeout"
    sent = 0
    search_from = 0
    try:
        deadline = time.monotonic() + timeout
        # Wait for each prompt (the terminal is configured by the first one)
        while (
            time.monotonic() < deadline
            and process.poll() is None
            and sent < len(key_presses)
        ):
            ready, _, _ = select.select([process.stdout], [], [], 0.2)
            if ready:
                chunk = os.read(process.stdout.fileno(), 4096)
                if not chunk:
                    break
                stdout += chunk
            prompt, key = key_presses[sent]
            position = stdout.find(prompt.encode(), search_from)
            if position >= 0:
                time.sleep(0.5)
                os.write(master_fd, key)
                search_from = position + len(prompt)
                sent += 1
        if sent == len(key_presses):
            status = "success"
        remaining = max(deadline - time.monotonic(), 1)
        out, err = process.communicate(timeout=remaining)
        stdout += out
        if status == "success" and process.returncode != 0:
            status = "failed"
        execution_context["stderr"] = err
    except subprocess.TimeoutExpired:
        process.kill()
        out, err = process.communicate()
        stdout += out
        execution_context["stderr"] = err
        status = "timeout"
    finally:
        os.close(master_fd)
    execution_context["stdout"] = stdout
    execution_context["status"] = status


@when(
    parsers.parse(
        "running the python '{file_name}' Kortex API example "
        "and pressing ESC once '{prompt}' is displayed"
    )
)
def python_run_and_press_escape(
    file_name: str, prompt: str, execution_context
):
    """Run the python file and press ESC once the prompt is displayed.

    *Args*:
        - file_name (string): Path and file name of the python file.
        - prompt (string): Text of the output after which ESC is pressed.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    run_python_with_key_presses(
        file_name, [(prompt, ESC_KEY)], execution_context
    )


@when(
    parsers.parse(
        "running the python '{file_name}' Kortex API example, "
        "pressing '{key}' once '{prompt}' is displayed "
        "and ESC once '{done}' is displayed"
    )
)
def python_run_and_press_key_then_escape(
    file_name: str, key: str, prompt: str, done: str, execution_context
):
    """Run the python file, press a key, then press ESC.

    *Args*:
        - file_name (string): Path and file name of the python file.
        - key (string): Key pressed once the prompt is displayed (ex: '9').
        - prompt (string): Text of the output after which the key is pressed.
        - done (string): Text of the output after which ESC is pressed.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    run_python_with_key_presses(
        file_name,
        [(prompt, key.encode()), (done, ESC_KEY)],
        execution_context,
    )


@then("the Kortex API example was run successfully")
def checks_api_execution_status(results_tracker, execution_context):
    """Check the API execution status.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = "success"
    results_tracker[0]["actual"] = execution_context["status"]


@then("the python Kortex API creation returns:")
def assert_output_of_api_creation(
    results_tracker, execution_context, datatable
):
    """Assert the output of the API Creation example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
        - datatable (string): Content of the output parameters.
    """
    pattern = (
        r"Creating\ssession\sfor\scommunication\\nSession\s(\w+)\\n"
        r"device_type:\s(\w+)\\n\\n"
        r"active_state:\s(\w+)\\n"
        r"connection\s\{\\n(?:\s+connection_identifier:\s\d+\\n)?\}\\n\\n"
    )
    group_index = 1

    match = search_output(pattern, execution_context)
    for row in datatable[0:]:
        results_tracker[group_index - 1]["param"] = row[0]
        results_tracker[group_index - 1]["expected"] = row[1]
        results_tracker[group_index - 1]["actual"] = match.group(group_index)
        group_index += 1


@then("the python Kortex protobuf object manipulation output is valid")
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
        r"Sequence ID with index : 10\\n"
        r"Sequence ID with index : 20\\n"
        r"Sequence ID with object iterator : 10\\n"
        r"Sequence ID with object iterator : 20\\n"
        r"Content ssid_2: 123\\n"
        r"Content ssid_3: \\n"
        r"Json object:\\n"
        r"\{\\n"
        r'  "name": "A Name",\\n'
        r'  "tasks": \[\\n'
        r"    \{\\n"
        r'      "groupIdentifier": 10\\n'
        r"    \},\\n"
        r"    \{\\n"
        r'      "groupIdentifier": 20\\n'
        r"    \},\\n"
        r"    \{\\n"
        r'      "groupIdentifier": 30\\n'
        r"    \},\\n"
        r"    \{\\n"
        r'      "groupIdentifier": 40\\n'
        r"    \},\\n"
        r"    \{\\n"
        r'      "groupIdentifier": 50\\n'
        r"    \}\\n"
        r"  \]\\n"
        r"\}\\n"
        r"Text format:\\n"
        r'name: "A Name"\\n'
        r"tasks \{\\n"
        r"  group_identifier: 10\\n"
        r"\}\\n"
        r"tasks \{\\n"
        r"  group_identifier: 20\\n"
        r"\}\\n"
        r"tasks \{\\n"
        r"  group_identifier: 30\\n"
        r"\}\\n"
        r"tasks \{\\n"
        r"  group_identifier: 40\\n"
        r"\}\\n"
        r"tasks \{\\n"
        r"  group_identifier: 50\\n"
        r"\}"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the python Kortex api mechanism output is valid")
def assert_output_of_api_mechanism(results_tracker, execution_context):
    """Assert the output of the API mechanism example (list of arm actions).

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """

    def action_block(identifier: int) -> str:
        """Return the regex of the block of the action with this identifier."""
        return (
            r"={44}\\n"
            r"Action name: \w+\\n"
            rf"Action identifier: {identifier}\\n"
            r"Action type: \w+\\n"
            r"Action permissions: \\n"
            r"(?:\\t| )+- \w+\\n"
            r"={44}\\n"
        )

    pattern = (
        r"Logging as admin on device (?:\d{1,3}\.){3}\d{1,3}\\n"
        r"List of all actions in the arm:\\n"
        + "".join(action_block(i) for i in range(1, 5))
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the python Kortex API error management returns:")
def assert_output_of_error_management(
    results_tracker, execution_context, datatable
):
    """Assert the output of the API error management example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
        - datatable (string): Content of the output parameters.
    """
    pattern = (
        r"Logging as admin on device (?:\d{1,3}\.){3}\d{1,3}\\n"
        r"Error_code:(\d+) , Sub_error_code:(\d+) \\n"
        r"Caught expected error: Server error name=(\w+), sub name=(\w+) "
        r"=> Empty username \\n\\n"
    )

    group_index = 1

    match = search_output(pattern, execution_context)
    for row in datatable[0:]:
        results_tracker[group_index - 1]["param"] = row[0]
        results_tracker[group_index - 1]["expected"] = row[1]
        results_tracker[group_index - 1]["actual"] = match.group(group_index)
        group_index += 1


@then("the python Kortex API notification output is valid")
def assert_output_of_api_notification(results_tracker, execution_context):
    """Assert the output of the API notification example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    pattern = (
        r"Logging as admin on device (?:\d{1,3}\.){3}\d{1,3}\\n"
        r"Subscribing to ConfigurationChange notifications\\n"
        r"Creating user profile to trigger notification\\n"
        r"User \w+ created\\n"
        r"\*{28}\\n"
        r"\* Callback function called \*\\n"
        r"\{\\n"
        r'  "event": "CONFIGURATION_CREATED",\\n'
        r'  "timestamp": \{\\n'
        r'    "sec": \d+,\\n'
        r'    "usec": \d+\\n'
        r"  \},\\n"
        r'  "userHandle": \{\\n'
        r'    "identifier": \d+\\n'
        r"  \},\\n"
        r'  "userProfileHandle": \{\\n'
        r'    "identifier": \d+\\n'
        r"  \},\\n"
        r'  "connection": \{\\n'
        r'    "userHandle": \{\\n'
        r'      "identifier": \d+\\n'
        r"    \},\\n"
        r'    "connectionInformation": '
        r'"type=TCP;ip=(?:\d{1,3}\.){3}\d{1,3};port=\d+",\\n'
        r'    "connectionIdentifier": \d+\\n'
        r"  \}\\n"
        r"\}\\n"
        r"\*{28}\\n"
        r"Now unsubscribing from ConfigurationChange notifications\\n"
        r"Deleting previously created user profile \(jcash\)\\n"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the python Kortex API device routine output is valid")
def assert_output_of_api_device_routine(results_tracker, execution_context):
    """Assert the output of the API device routine example (device list).

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    device_block = (
        r"-{29}\\n"
        r"-- \w+: id = \d+ --\\n"
        r" +deviceType: \w+\\n"
        r" +firmwareVersion: \d+\\n"
        r" +bootloaderVersion: \d+\\n"
        r" +modelNumber: [\w-]+\\n"
        r" +partNumber: [\w-]+\\n"
        r" +partNumberRevision: \d+\\n"
        r" +serialNumber: [\w-]+\\n"
        r" +macAddress: (?:[0-9A-F]{2}:){5}[0-9A-F]{2}\\n"
    )
    pattern = (
        r"Logging as admin on device (?:\d{1,3}\.){3}\d{1,3}\\n"
        rf"(?:{device_block})+"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the python Kortex API protection zones configuration output is valid")
def assert_output_of_api_protection_zones_configuration(results_tracker, execution_context):
    """Assert the output of the API device routine example (device list).

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    number = r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"
    safe_position = (
        r"Moving the arm to a safe position\\n"
        r"EVENT : ACTION_START\\n"
        r"(?:EVENT : ACTION_FEEDBACK\\n)*"
        r"EVENT : ACTION_END\\n"
    )
    zones = (
        r"PROTECTION ZONES\\n"
        r"(?:Protection Zone : [\w ]+ "
        rf"Origin : \[ (?:{number} ){{3}}\] "
        rf"Dimensions : \[ (?:{number} )+\]\\n)+"
    )
    cartesian_move = (
        r"Starting Cartesian action movement \.\.\.\\n"
        r"Executing action\\n"
        r"Waiting for movement to finish \.\.\.\\n"
        r"EVENT : ACTION_START\\n"
        r"(?:EVENT : ACTION_FEEDBACK\\n)*"
        r"EVENT : ACTION_END\\n"
        r"Cartesian movement completed\\n"
        r"Moving towards the protection zone for \d+ seconds\.\.\.\\n"
        r"Stopping the robot\.\.\.\\n"
    )
    pattern = (
        r"Logging as admin on device (?:\d{1,3}\.){3}\d{1,3}\\n"
        rf"{safe_position}{zones}"
        rf"(?:{cartesian_move}{safe_position}{zones})+"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the python Kortex API move angular and cartesian output is valid")
def assert_output_of_api_move_angular_and_cartesian(
    results_tracker, execution_context
):
    """Assert the output of the move angular and cartesian example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """

    def movement(kind: str) -> str:
        """Return the regex of the block of a movement of this kind."""
        return (
            rf"Starting (?i:{kind}) action movement \.\.\.\\n"
            r"Executing action\\n"
            r"Waiting for movement to finish \.\.\.\\n"
            r"EVENT : ACTION_START\\n"
            r"(?:EVENT : ACTION_FEEDBACK\\n)*"
            r"EVENT : ACTION_END\\n"
            rf"{kind} movement completed\\n"
        )

    pattern = (
        r"Logging as admin on device (?:\d{1,3}\.){3}\d{1,3}\\n"
        r"Moving the arm to a safe position\\n"
        r"EVENT : ACTION_START\\n"
        r"(?:EVENT : ACTION_FEEDBACK\\n)*"
        r"EVENT : ACTION_END\\n"
        r"Safe position reached\\n"
        rf"{movement('Cartesian')}{movement('Angular')}"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the python Kortex API sequence output is valid")
def assert_output_of_api_sequence(results_tracker, execution_context):
    """Assert the output of the API sequence example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    pattern = (
        r"Logging as admin on device (?:\d{1,3}\.){3}\d{1,3}\\n"
        r"Moving the arm to a safe position\\n"
        r"EVENT : ACTION_START\\n"
        r"(?:EVENT : ACTION_FEEDBACK\\n)*"
        r"EVENT : ACTION_END\\n"
        r"Creating Action for Sequence\\n"
        r"Creating angular action\\n"
        r"Creating Cartesian action\\n"
        r"Creating Sequence\\n"
        r"Appending Actions to Sequence\\n"
        r"Creating sequence on device and executing it\\n"
        r"Waiting for movement to finish \.\.\.\\n"
        r"(?:Sequence task \d+ completed\\n)+"
        r"Sequence completed\.\\n"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the python Kortex API twist command output is valid")
def assert_output_of_api_twist_command(results_tracker, execution_context):
    """Assert the output of the API twist command example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    pattern = (
        r"Logging as admin on device (?:\d{1,3}\.){3}\d{1,3}\\n"
        r"Moving the arm to a safe position\\n"
        r"EVENT : ACTION_START\\n"
        r"(?:EVENT : ACTION_FEEDBACK\\n)*"
        r"EVENT : ACTION_END\\n"
        r"Safe position reached\\n"
        r"Sending the twist command for \d+ seconds\.\.\.\\n"
        r"Stopping the robot\.\.\.\\n"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the python Kortex API send joint speeds output is valid")
def assert_output_of_api_send_joint_speeds(results_tracker, execution_context):
    """Assert the output of the API send joint speeds example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    pattern = (
        r"Logging as admin on device (?:\d{1,3}\.){3}\d{1,3}\\n"
        r"Reaching joint angles\.\.\.\\n"
        r"Waiting for movement to finish \.\.\.\\n"
        r"EVENT : ACTION_START\\n"
        r"(?:EVENT : ACTION_FEEDBACK\\n)*"
        r"EVENT : ACTION_END\\n"
        r"Joint angles reached\\n"
        r"Sending the joint speeds for \d+ seconds\.\.\.\\n"
        r"Stopping the robot\\n"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the python Kortex API UART bridge output is valid")
def assert_output_of_api_uart_bridge(results_tracker, execution_context):
    """Assert the output of the API UART bridge example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    pattern = (
        r"Logging as admin on device (?:\d{1,3}\.){3}\d{1,3}\\n"
        r"Found the Interconnect on device identifier \d+\\n"
        r"UARTBridge ID # \d+ created between Interconnect "
        r"\(dev# \d+\)'s port #\d+ and external port #\d+\\n"
        r"UART bridge object initialized\\n"
        r"Waiting 10 seconds for data from uart\.\.\.\\n"
        r"Received data : "
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the python Kortex API GPIO bridge output is valid")
def assert_output_of_api_gpio_bridge(results_tracker, execution_context):
    """Assert the output of the API GPIO bridge example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    gpio_cycle = (
        r"GPIO pin GPIO_IDENTIFIER_1 will be put at value "
        r"GPIO_VALUE_(?:HIGH|LOW)\\n"
        r"GPIO pin GPIO_IDENTIFIER_2 will be put at value "
        r"GPIO_VALUE_(?:HIGH|LOW)\\n"
        r"Value read for pin #3 is : [01]\\n"
        r"Value read for pin #4 is : [01]\\n"
    )
    pattern = (
        r"Logging as admin on device (?:\d{1,3}\.){3}\d{1,3}\\n"
        r"Found the Interconnect on device identifier \d+\\n"
        r"(?:Setting pin #\d+ as (?:output|input pullup)\.\.\.\\n)+"
        r"GPIO bridge object initialized\\n"
        rf"(?:{gpio_cycle})+"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the python Kortex API I2C bridge output is valid")
def assert_output_of_api_i2c_bridge(results_tracker, execution_context):
    """Assert the output of the API I2C bridge example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    error = (
        r"Error : Server error name=\w+, sub name=\w+ => +"
        r"(?:\\n)+"
    )
    pattern = (
        r"Logging as admin on device (?:\d{1,3}\.){3}\d{1,3}\\n"
        r"Found the Interconnect on device identifier \d+\\n"
        r"I2C bridge object initialized\\n"
        rf"Reading byte array from interconnect I2C bus\.\.\.\\n{error}"
        rf"Sending byte array to interconnect I2C bus\.\.\.\\n{error}"
        rf"Reading byte array from interconnect I2C bus\.\.\.\\n{error}"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the python Kortex API gripper command output is valid")
def assert_output_of_api_gripper_command(results_tracker, execution_context):
    """Assert the output of the API gripper command example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    number = r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"
    pattern = (
        r"Logging as admin on device (?:\d{1,3}\.){3}\d{1,3}\\n"
        r"Performing gripper test in position\.\.\.\\n"
        r"(?:Going to position \d+\.\d{2}\.\.\.\\n)+"
        r"Opening gripper using speed command\.\.\.\\n"
        rf"(?:Current position is : {number}\\n)+"
        r"Closing gripper using speed command\.\.\.\\n"
        rf"(?:Current speed is : {number}\\n)+"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the python Kortex API gripper low level command output is valid")
def assert_output_of_api_gripper_low_level_command(
    results_tracker, execution_context
):
    """Assert the output of the API gripper low level command example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    number = r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"
    pattern = (
        r"Logging as admin on device (?:\d{1,3}\.){3}\d{1,3}\\n"
        rf"(?:Position = +{number}\\n)+"
        r"Press keys '0' to '9' to change gripper position\. "
        r"Press ESC to quit\.\\n"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then(
    parsers.parse(
        "the python Kortex API gripper low level command output is valid "
        "after pressing '{key}'"
    )
)
def assert_output_of_api_gripper_low_level_command_key(
    key: str, results_tracker, execution_context
):
    """Assert the output of the gripper low level command after a key press.

    Pressing the key '0' to '9' sends the gripper to the position
    ``(key + 1) * 10``.

    *Args*:
        - key (string): Key ('0' to '9') pressed during the example.
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    target_position = (int(key) + 1) * 10
    number = r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"
    pattern = (
        r"Logging as admin on device (?:\d{1,3}\.){3}\d{1,3}\\n"
        rf"(?:Position = +{number}\\n)+"
        r"Press keys '0' to '9' to change gripper position\. "
        r"Press ESC to quit\.\\n"
        rf"Going to position {target_position}\\n"
        r"Target reached\\n"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the python Kortex API torque control cyclic output is valid")
def assert_output_of_api_torque_control_cyclic_command(
    results_tracker, execution_context
):
    """Assert the output of the API gripper low level command example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    # The cyclic part runs in a thread of the example, so its messages can
    # come in a different order from one run to the other (and the example
    # can even be stopped before the end of the 30 seconds). Only the
    # presence of each message is checked after "Init Cyclic". The messages
    # of the two threads can also be mixed on the same line.
    pattern = (
        r"(?:Logging as admin on device (?:\d{1,3}\.){3}\d{1,3}\\n)+"
        r"Moving the arm to a safe position\\n"
        r"Waiting for movement to finish \.\.\.\\n"
        r"EVENT : ACTION_START\\n"
        r"(?:EVENT : ACTION_FEEDBACK\\n)*"
        r"EVENT : ACTION_END\\n"
        r"Cartesian movement completed\\n"
        r"Init Cyclic\\n"
        r"(?=.*Run Cyclic)"
        r"(?=.*Running torque control example for \d+ seconds)"
        r"(?=.*Stopping the cyclic and putting the arm back in position "
        r"mode\.\.\.)"
        r"(?=.*Clean Exit)"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the python Kortex API Gen3 ethernet bridge output is valid")
def assert_output_of_api_gen3_ethernet_bridge_command(
    results_tracker, execution_context
):
    """Assert the output of the API Gen3 ethernet bridge command example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    pattern = (
        r"(?:Logging as admin on device (?:\d{1,3}\.){3}\d{1,3}\\n)+"
        r"Found the Interconnect on device identifier \d+\\n"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then("the python Kortex API send angular waypoint trajectory output is valid")
def assert_output_of_api_send_angular_waypoint_trajectory_command(
    results_tracker, execution_context
):
    """Assert the output of the send angular waypoint trajectory example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    pattern = (
        r"Logging as admin on device (?:\d{1,3}\.){3}\d{1,3}\\n"
        r"Moving the arm to a safe position\\n"
        r"EVENT : ACTION_START\\n"
        r"(?:EVENT : ACTION_FEEDBACK\\n)*"
        r"EVENT : ACTION_END\\n"
        r"Safe position reached\\n"
        r"Reaching angular pose trajectory\.\.\.\\n"
        r"Waiting for trajectory to finish \.\.\.\\n"
        r"(?:EVENT : ACTION_PREPROCESS_END\\n)?"
        r"EVENT : ACTION_START\\n"
        r"(?:EVENT : ACTION_FEEDBACK\\n)*"
        r"EVENT : ACTION_END\\n"
        r"Angular movement completed\\n"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then(
    "the python Kortex API send cartesian waypoint trajectory output is valid"
)
def assert_output_of_api_send_cartesian_waypoint_trajectory(
    results_tracker, execution_context
):
    """Assert the output of the send cartesian waypoint trajectory example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    action_events = (
        r"EVENT : ACTION_START\\n"
        r"(?:EVENT : ACTION_FEEDBACK\\n)*"
        r"EVENT : ACTION_END\\n"
    )
    trajectory_events = (
        r"Waiting for trajectory to finish \.\.\.\\n"
        r"(?:EVENT : ACTION_PREPROCESS_END\\n)?"
        rf"{action_events}"
    )
    pattern = (
        r"Logging as admin on device (?:\d{1,3}\.){3}\d{1,3}\\n"
        r"Moving the arm to a safe position\\n"
        rf"{action_events}"
        r"Safe position reached\\n"
        r"Moving cartesian trajectory\.\.\.\\n"
        rf"{trajectory_events}"
        r"Cartesian trajectory with no optimization completed +\\n"
        rf"{trajectory_events}"
        r"Cartesian trajectory with optimization completed +\\n"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then(
    "the python Kortex API compute kinematics output is valid"
)
def assert_output_of_api_compute_kinematics(
    results_tracker, execution_context
):
    """Assert the output of the compute kinematics example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    number = r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"
    joint_angles = (
        r"Joint ID : Joint Angle\\n"
        rf"(?:\d+ +: +{number}\\n)+"
    )
    pattern = (
        rf"{joint_angles}"
        r"\\n"
        r"Computing Foward Kinematics using joint angles\.\.\.\\n"
        r"Pose calculated : +\\n"
        rf"Coordinate \(x, y, z\) +: \(({number}, ){{2}}{number}\)\\n"
        r"Theta \(theta_x, theta_y, theta_z\) +: "
        rf"\(({number}, ){{2}}{number}\)\\n"
        r"\\n"
        r"Computing Inverse Kinematics using joint angles and pose\.\.\.\\n"
        rf"{joint_angles}"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then(
    "the python Kortex API vision intrinsics output is valid"
)
def assert_output_of_api_vision_intrinsics(
    results_tracker, execution_context
):
    """Assert the output of the vision intrinsics example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    number = r"-?\d+\.\d+"
    resolution = r"\d+x\d+"

    # The example prints a blank line before each title (the last line of the
    # output is followed by a single line break only)
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
        r"Logging as admin on device (?:\d{1,3}\.){3}\d{1,3}\\n"
        r"Vision module found, device Id: \d+\\n"
        r"\\n\\n\*\* Example showing how to retrieve the intrinsic parameters "
        r"of the Color and Depth sensors \*\*\\n"
        rf"{get_block('get intrinsic parameters of active color resolution')}"
        rf"{get_block('get intrinsic parameters of active depth resolution')}"
        rf"{get_block(f'get intrinsic parameters for color resolution {resolution}')}"
        rf"{get_block(f'get intrinsic parameters for depth resolution {resolution}')}"
        r"\\n\\n\*\* Example showing how to set the intrinsic parameters of "
        r"the Color and Depth sensors \*\*\\n"
        + "".join(
            get_block(f"get current intrinsic parameters for {sensor} resolution {resolution}")
            + set_line(f"set new intrinsic parameters for {sensor} resolution {resolution}")
            + get_block(f"get new intrinsic parameters for {sensor} resolution {resolution}")
            + set_line(f"set back old intrinsic parameters for {sensor} resolution {resolution}")
            for sensor in ("color", "depth")
        )
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then(
    "the python Kortex API vision extrinsics output is valid"
)
def assert_output_of_api_vision_extrinsics(
    results_tracker, execution_context
):
    """Assert the output of the vision extrinsics example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    number = r"-?\d+\.\d+"
    row = rf"{number}(?: +{number}){{2}}"

    # The example prints a blank line before each title (the last line of the
    # output is followed by a single line break only)
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
        r"Logging as admin on device (?:\d{1,3}\.){3}\d{1,3}\\n"
        r"Vision module found, device Id: \d+\\n"
        r"\\n\\n\*\* Example showing how to retrieve the extrinsic parameters "
        r"\*\*\\n"
        rf"{get_block('get extrinsic parameters')}"
        r"\\n\\n\*\* Example showing how to set the extrinsic parameters "
        r"\*\*\\n"
        rf"{get_block('get current extrinsic parameters')}"
        rf"{set_line('set new extrinsic parameters')}"
        rf"{get_block('get new extrinsic parameters')}"
        rf"{set_line('set back old extrinsic parameters')}"
    )

    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = True
    results_tracker[0]["actual"] = bool(
        search_output(pattern, execution_context)
    )


@then(
    "the python Kortex API vision sensor focus action output is valid"
)
def assert_output_of_api_vision_sensor_focus_action(
    results_tracker, execution_context
):
    """Assert the output of the vision sensor focus action example.

    *Args*:
        - results_tracker (fixture): Generic result comparaison fixture.
        - execution_context (fixture): A fixture that contains the execution
        output, error and status
    """
    wait = r"-- Waiting for 10 seconds to observe the effects of the focus action\.\.\. --"

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
        """Title of an example, preceded by a blank line."""
        return rf"\\n\*\* Example showing how to {re.escape(title)} \*\*\\n"

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
        r"Logging as admin on device (?:\d{1,3}\.){3}\d{1,3}\\n"
        r"Vision module found, device Id: \d+\\n"
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


@then(
    "the python Kortex API vision sensor options output is valid"
)
def assert_output_of_api_vision_sensor_options(
    results_tracker, execution_context
):
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

    information = (
        rf"(?:Option id: \d+  name: {option}  is_writable: (?:True|False)\\n"
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
    # it could not read back. The device answers INVALID_PARAM for the gain
    # (a known behaviour, to be confirmed). It is accepted here, as in the
    # reference output, but any other option failing is not.
    gain_not_read = (
        r"Failed to get value for option 'OPTION_GAIN': "
        r"Server error name=ERROR_DEVICE, sub name=INVALID_PARAM => *\\n\\n"
    )
    restored_values = rf"(?:{confirm_line}|{gain_not_read})+"

    def set_and_confirm(value: str, sensor: str, confirmed=confirm_values):
        return (
            vision(f"set {value} value for all {sensor} sensor options")
            + set_values
            + vision(
                f"confirm {value} value was set for all {sensor} sensor "
                "options"
            )
            + confirmed
        )

    wait_color = title(
        "Waiting for 5 seconds to observe the effects of the new COLOR "
        "sensor options values..."
    )

    pattern = (
        r"Logging as admin on device (?:\d{1,3}\.){3}\d{1,3}\\n"
        r"Vision module found, device Id: \d+\\n"
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