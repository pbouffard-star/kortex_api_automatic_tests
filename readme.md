# Kortex API automatic tests

Automated validation of the Kinova Kortex API examples (Python and C++) against a Gen3 robot.

Each example is run as a subprocess. Its output is compared with a regular expression, and the
results are reported with `pytest-bdd` (Gherkin scenarios).

> **Jenkins status.** `jenkins/jenkinsfile` describes the full pipeline, but **no Jenkins node is
> configured for it yet**, so it cannot be run under Jenkins today. Use the jenkinsfile as a
> reference: every stage is explained below with the commands to run it **manually** from a
> terminal, or with the **VS Code debug configuration** for the validation stage.

## Contents

1. [Repository layout](#repository-layout)
2. [Prerequisites](#prerequisites)
3. [Jenkins stages, run manually](#jenkins-stages-run-manually)
4. [Running the validation](#running-the-validation)
5. [Writing or changing a test](#writing-or-changing-a-test)
6. [Troubleshooting](#troubleshooting)

## Repository layout

```
api_python/             Kortex Python examples   (NOT tracked by git, see .gitignore)
api_cpp/                Kortex C++ examples      (NOT tracked by git, see .gitignore)
kortex/API/<version>/   Downloaded kortex_api wheel(s) (ignored by git)
feature_files/
    python.feature      One scenario per Python example
    cpp.feature         One scenario per C++ example
validation/
    scenarios.py        Generates one pytest test per scenario of the feature files
    conftest.py         Fixtures, per-step PASS/FAIL tracking, JSON report metadata
    steps/run_python.py Steps that run the Python examples and check their output
    steps/run_cpp.py    Steps that run the compiled C++ examples and check their output
    scripts/fail_analysis.py   Reads the JSON report and flags unanalysed failures
    requirements.txt    Python packages of the test framework
    pytest.ini          Markers and log settings
jenkins/jenkinsfile     Declarative pipeline (reference, see above)
.vscode/launch.json     "Run Automated Validation" debug configuration
```

`api_python/` and `api_cpp/` are the Kortex example folders from: 
https://github.com/Kinovarobotics/Kinova-kortex2_Gen3_G3L. They are ignored by git, so they must be
present in your working copy. The tests read them through the relative paths `../api_python/examples`
 and `../api_cpp/examples/build`, which means
**pytest must be started from the `validation/` folder**.

## Prerequisites

| Need | Detail |
| --- | --- |
| OS | Ubuntu 24.04 (the Jenkins agent label is `ubuntu24.04`) |
| Python | 3.9 (`python3.9`), the examples and the wheel are run with it |
| C++ | `cmake` and a C++ compiler, to build the C++ examples |
| JFrog CLI | `jf`, with access to `https://artifactory.kinovaapps.com` |
| Robot | A Gen3 reachable at `192.168.1.10` (user `admin` / password `admin`) |
| SSH | Root SSH key of the robot, only for the firmware install stage |

The examples take `--ip`, `-u` and `-p` arguments. The tests run them **without arguments**, so they
use the defaults `192.168.1.10`, `admin`, `admin`. If your robot uses another address, change the
defaults in the examples' `utilities.py` / `utilities.cpp`.

The local development environment is the pyenv virtual environment `kts-robot-3.9` (see
`.python-version` and `.vscode/settings.json`). The pipeline uses a `.venv` instead. Either works.

## Jenkins stages, run manually

The pipeline has seven stages, run in this order. The variables below are the ones used by the
jenkinsfile:

```bash
export GEN3_IP=192.168.1.10
export GEN3_SSH_KEY=~/.ssh/gen3-sut-ci     # the pipeline uses /home/adminkinova/.ssh/gen3-sut-ci
```

### 1. Checkout

Jenkins checks the repository out and records the commit hash for the build description.

```bash
git clone <repository-url> kortex_api_automatic_tests && cd kortex_api_automatic_tests
git rev-parse HEAD
```

### 2. Configure JFrog CLI

The pipeline uses the JFrog CLI configuration already on the machine (`~/.jfrog`). If there is none
(`jf c show` prints nothing), it adds a configuration with the Jenkins credential.

```bash
jf c show                    # if this prints a configuration, you are done
# otherwise, with your own Artifactory credentials:
jf c add kinova --url="https://artifactory.kinovaapps.com" \
    --user="<user>" --password="<password>" --interactive=false --overwrite
jf c use kinova
```

### 3. Python Environement Set Up

Installs Python 3.9 from the deadsnakes PPA, creates a virtual environment and installs the
requirements.

```bash
sudo apt update
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.9 python3.9-venv python3.9-dev -y

python3.9 -m venv .venv
.venv/bin/pip install -r validation/requirements.txt
```

### 4. Fetch the Latest GEN3 SWU

Looks up the newest firmware (`.swu`) of the `development` branch in Artifactory and keeps its build
number in `GEN3_VERSION`, then downloads it to the workspace.

```bash
# Find the newest build (prints JSON; build.number is in props)
jf rt s --sort-by created --sort-order desc --fail-no-op --limit 1 \
    --props branch_name=development \
    "generic-local-build/kortex/products/gen3/development/*/Gen3*.swu"
export GEN3_VERSION=<build.number from the search result>

# Download it (the file is named Gen3*.swu, in the current folder)
jf rt dl --sort-by created --sort-order desc --fail-no-op --limit 1 --flat \
    --props branch_name=development \
    "generic-local-build/kortex/products/gen3/development/*/Gen3*.swu"
```

### 5. Fetch the Latest Kortex and install

Downloads the newest `kortex_api` wheel into `kortex/API/<version>/` and installs it in the `.venv`.

```bash
jf rt dl "generic-public/kortex/API/*/kortex_api-*.post3-py3-none-any.whl" \
    --sort-by=created --sort-order=desc --limit=1

ls kortex/API                                  # the folder name is the version
export KORTEX_VERSION=<version folder>
.venv/bin/pip install kortex/API/${KORTEX_VERSION}/*.whl
```

### 6. Install latest GEN3 SWU

Copies the firmware to the robot, flashes it and reboots. **This replaces the firmware on the robot.**
Skip it when you only want to test against the firmware already installed.

```bash
ssh-keyscan -H ${GEN3_IP} > known_hosts 2>/dev/null
[ -s known_hosts ] || { echo "No SSH host key from ${GEN3_IP} - is the board powered and reachable?"; exit 1; }

SSH_OPTS="-o UserKnownHostsFile=known_hosts -o BatchMode=yes -o IdentitiesOnly=yes -i ${GEN3_SSH_KEY}"

SWU_FILE=$(ls -t Gen3*.swu | head -n 1)      # the file downloaded in stage 4
scp ${SSH_OPTS} "${SWU_FILE}" root@${GEN3_IP}:/mnt/download/firmware.swu
ssh ${SSH_OPTS} root@${GEN3_IP} './opt/armbase/scripts/flash_swu.sh; reboot'
```

Wait for the robot to reboot (about a minute or two) before the next stage.

### 7. Run Automated Validation

The pipeline builds the C++ examples, then runs all the scenarios (Python and C++) with pytest. The
tests start the Python examples with `python3.9` taken from the `PATH`, so the `.venv` is put first
in the `PATH` to use the interpreter that has `kortex_api`. Do it manually like this:

```bash
# Build the C++ examples (one executable per example, in api_cpp/examples/build)
cd api_cpp/examples && cmake -B build && cmake --build build && cd ../..

# Run the scenarios, from validation/
export PATH="$PWD/.venv/bin:$PATH"
cd validation
python3.9 -m pytest scenarios.py -v \
    --json-report --json-report-file=./TestMetrics/json/TestReport.json \
    --html=report.html --self-contained-html \
    --junitxml=results.xml
```

See [Running the validation](#running-the-validation) for filters and the debug configuration.

### Post actions

After the stages, Jenkins publishes `validation/results.xml` (JUnit), sets the build description and
cleans the workspace. Manually you only need the generated reports (listed below).

## Running the validation

Run everything from the `validation/` folder with the environment that has `kortex_api` installed.

### From VS Code (debug script)

Use the **Run Automated Validation** configuration (`.vscode/launch.json`, Run and Debug panel).
It asks for a **tag filter** (default `python`), runs

```
pytest scenarios.py -v -k <filter> --json-report ... --html=report.html --junitxml=results.xml
```

from `validation/` with the `kts-robot-3.9` interpreter, and lets you set breakpoints in the steps.

### From a terminal

```bash
cd validation
python3.9 -m pytest scenarios.py -v -k python          # all Python scenarios
python3.9 -m pytest scenarios.py -v -k cpp             # all C++ scenarios
python3.9 -m pytest scenarios.py -v -k "gripper"       # only the gripper scenarios
python3.9 -m pytest scenarios.py -v -k "notification"  # one scenario, by name
python3.9 -m pytest scenarios.py -v -k "python and not gripper"
python3.9 -m pytest scenarios.py -s -k "<name>"        # -s shows the raw output on a mismatch
```

`-k` matches the scenario name and its tags. Scenario test names are the scenario title in lower
case with underscores, prefixed with `test_`.

### Tags

| Tag | Meaning |
| --- | --- |
| `@python`, `@cpp` | Feature-level tags (one per feature file) |
| `@gripper` | Needs a gripper installed on the robot (the gripper scenarios move it) |
| `@daily`, `@weekly` | Jenkins run filters (a scenario without one counts as `daily`) |
| `@skip_<reason>` | Skips the scenario with the reason after `skip_` |

### Reports

| File | Content |
| --- | --- |
| `validation/results.xml` | JUnit report (what Jenkins publishes) |
| `validation/report.html` | Self-contained HTML report |
| `validation/TestMetrics/json/TestReport.json` | JSON report, with the steps of each scenario |
| `validation/pytest.log` | Log of the run |

These files are ignored by git.

### Failure analysis

`validation/scripts/fail_analysis.py` reads the JSON report and exits with code `1` if a scenario
failed and `2` if a scenario unexpectedly passed (`XPASS`):

```bash
python3.9 validation/scripts/fail_analysis.py validation/TestMetrics/json/TestReport.json
```

### What a failure looks like

When an output pattern does not match, the test prints the status, the raw `stdout` and the `stderr`
of the example, for example:

```
Output did not match the expected pattern. Status: success
stdout: b'...'
```

`Status` is `success`, `failed` (non-zero exit), `timeout` or `File Not Found` (C++ executable not
built). Compare the printed `stdout` with the pattern in the matching `then` step.

## Writing or changing a test

A test is a scenario in a feature file plus its steps:

```gherkin
Scenario: Test to run in Cpp the Kortex API called notification
    When running the C++ '000-Getting_started/05-notification.cpp' Kortex API example with a timeout of 15 seconds
    Then the Kortex API example was run successfully
    Then the C++ Kortex API notification output is valid
```

- **`When` steps** run the example and store its output. Variants:
  - `running the python '<file>' Kortex API example` (default timeout 60 s)
  - `running the C++ '<file>' Kortex API example` (default timeout **5 s**)
  - `... with a timeout of <N> seconds` (use it for examples that move the arm or sleep)
  - `running the python '<file>' Kortex API example and pressing ESC once '<prompt>' is displayed`
  - `running the python '<file>' Kortex API example, pressing '<key>' once '<prompt>' is displayed and ESC once '<done>' is displayed`
    (examples that read the keyboard run in a pseudo terminal, see the gripper low level scenario)
- **`Then` steps** check the output with a regular expression (`search_output`). The output is
  compared as a Python `bytes` text, so a line break is written `\\n` in the patterns. Use `\d+` or
  a number pattern for values that change between runs (timestamps, identifiers, positions).
- C++ examples must be built first. The executable of
  `000-Getting_started/01-api_creation.cpp` is `build/000-Getting_started_01-api_creation`.

## Troubleshooting

- **`File Not Found` status in a C++ scenario**: build the examples (stage 7) and run pytest from
  `validation/`.
- **A C++ scenario times out**: the default is 5 s. Add `with a timeout of <N> seconds` to the scenario.
- **`AttributeError: ... has no "duration" field`**: the examples were written for another API
  version. Match the examples to the installed `kortex_api` (`python3.9 -m pip show kortex-api`).
- **pip warns `mypy-protobuf requires protobuf>=...`**: `kortex_api` pins `protobuf` 3.5.1. Uninstall
  `mypy-protobuf` from this environment.
- **Cannot reach the robot**: check `ping 192.168.1.10`, the cable and the PC network settings
  (a static address in `192.168.1.x`).
- **`ssh-keyscan` returns nothing**: the robot is off or still rebooting.
- **Edits to the examples are not tracked**: `api_python/` and `api_cpp/` are ignored by git, so a
  fix made in an example (for example the `duration` lines or the `EVENT :` print of
  `02-protection_zones_configuration.cpp`) is lost if the folders are copied again.
