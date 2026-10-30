import subprocess
import pytest
from pytest_bdd import when, then, parsers

python_ex_file_path = "../api_python/examples"

@pytest.fixture
def execution_context():
    """A fixture to pass the execution output, error and status to an other step. """
    return {"stdout": "", "stderr": "", "status": "not_run"}


@when(parsers.parse("running the python '{file_name}' Kortex API example"))
def python_run(file_name: str, execution_context):
    ''' Runs the specified python file

    *Args*:
        - file_name (string): Path and file name of the python file.
    '''
    path = f'{python_ex_file_path}/{file_name}'
    try:
        result = subprocess.run(["python3.9", path], capture_output=True, timeout=5)
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


@then(parsers.parse("the Kortex API example was run successfully"))
def checks_api_execution_status(results_tracker, execution_context):
    ''' Checks the API execution status '''
    results_tracker[0]["param"] = "Output Message"
    results_tracker[0]["expected"] = "success"
    results_tracker[0]["actual"] = execution_context["status"]