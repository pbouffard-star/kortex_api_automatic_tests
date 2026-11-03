import subprocess
from pytest_bdd import when, parsers

# Folder where CMake puts the compiled examples (one executable per example)
cpp_build_path = "../api_cpp/examples/build"


@when(parsers.parse("running the c++ '{file_name}' Kortex API example"))
def cpp_run(file_name: str, execution_context):
    ''' Runs the prebuilt executable of the specified C++ example

        The CMake build names each executable after its source path, with '/' replaced by '_'
        and without the extension (ex: '000-Getting_started/01-api_creation.cpp' becomes
        '000-Getting_started_01-api_creation').

        *Args*:
            - file_name (string): Path and file name of the C++ source file of the example.
            - execution_context (fixture): A fixture that contains the execution output, error and status
    '''
    exe_name = file_name.removesuffix(".cpp").replace("/", "_")
    path = f'{cpp_build_path}/{exe_name}'
    try:
        result = subprocess.run([path], capture_output=True, timeout=5)
        execution_context["stdout"] = result.stdout
        execution_context["stderr"] = result.stderr
        execution_context["status"] = "success" if result.returncode == 0 else "failed"
    except subprocess.TimeoutExpired as e:
        execution_context["stdout"] = e.stdout or ""
        execution_context["stderr"] = e.stderr or ""
        execution_context["status"] = "timeout"
    except FileNotFoundError:
        execution_context["status"] = "File Not Found"
