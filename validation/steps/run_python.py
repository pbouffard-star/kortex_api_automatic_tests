import subprocess
import re
from pytest_bdd import when, then, parsers

python_ex_file_path = "../api_python/examples"


@when(parsers.parse("running the python '{file_name}' Kortex API example"))
def python_run(file_name: str, execution_context):
    ''' Runs the specified python file

        *Args*:
            - file_name (string): Path and file name of the python file.
            - execution_context (fixture): A fixture that contains the execution output, 
            error and status
    '''
    path = f'{python_ex_file_path}/{file_name}'
    try:
        result = subprocess.run(["python3.9", path],
                                capture_output=True, timeout=5)
        execution_context["stdout"] = result.stdout
        execution_context["status"] = "success"
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


@then("the Kortex API example was run successfully")
def checks_api_execution_status(results_tracker, execution_context):
    ''' Checks the API execution status

        *Args*:
            - results_tracker (fixture): Generic result comparaison fixture.
            - execution_context (fixture): A fixture that contains the execution output, 
            error and status
    '''
    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = "success"
    results_tracker[0]["actual"] = execution_context["status"]


@then("the Kortex API creation returns:")
def assert_output_of_api_creation(results_tracker, execution_context, datatable):
    ''' Asserts the output of the API Creation example

        *Args*:
            - results_tracker (fixture): Generic result comparaison fixture.
            - execution_context (fixture): A fixture that contains the execution output, 
            error and status
            - datatable (string): Content of the output parameters.
    '''
    pattern = r"Creating\ssession\sfor\scommunication\\nSession\s(\w+)\\ndevice_type:\s(\w+)\\n\\nactive_state:\s(\w+)\\nconnection\s\{\\n\s+connection_identifier:\s(\d*)\\n\}\\n\\n"
    group_index = 1

    match = re.search(pattern, str(execution_context["stdout"]))
    for row in datatable[0:]:
        results_tracker[group_index-1]["param"] = row[0]
        results_tracker[group_index-1]["expected"] = row[1]
        results_tracker[group_index-1]["actual"] = match.group(group_index)
        group_index += 1
