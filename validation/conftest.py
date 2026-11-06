#! /usr/bin/python3
"""Conftest file for global Pytest."""

import logging
import os
import re
import sys
from datetime import datetime

import pytest

logger = logging.getLogger(__name__)

# Add this folder to sys.path so that the local imports resolve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TrackerList(list):
    """List that auto-creates tracker dicts on index access.

    This removes the need to pre-size the list.
    """

    _template = {
        "param": None,
        "expected": None,
        "actual": None,
        "compairison": "equal_str",
        "step_result": None,
        "associated_bug": None,
    }

    def __getitem__(self, index):
        """Return the tracker at index, creating missing ones on demand."""
        while len(self) <= index:
            self.append(self._template.copy())
        return super().__getitem__(index)


@pytest.fixture
def results_tracker():
    """Create a dictionary list holding the comparison data (PASS or FAIL).

    Entries are created on demand when accessed by index.
    """
    return TrackerList()


@pytest.fixture
def execution_context():
    """Pass the execution output, error and status to another step."""
    return {"stdout": "", "stderr": "", "status": "not_run"}


def pytest_bdd_before_scenario(request, feature, scenario):
    """Store the Jenkins filter parameter and feature name of the scenario."""
    jenkins_filter = "daily"  # daily is the default

    for tag in sorted(scenario.tags):
        if tag in ("daily", "weekly"):
            jenkins_filter = tag

    request.node.bdd_scenario_filter = jenkins_filter
    request.node.bdd_feature_name = feature.name


def pytest_bdd_after_step(request, step, step_func_args, feature, scenario):
    """Fill the .json file with the info of each step.

    The info is the param, expected, actual and result of each single step.
    Takes account of the datatable if any.
    """
    if not hasattr(request.node, "bdd_steps_data"):
        request.node.bdd_steps_data = []

    if step.type in ("when", "given"):
        # Creating the step definition table dict and add in .json
        step_entry = {"step_name": step.name, "type": step.type}
        datatable = step_func_args.get("datatable")
        if datatable:
            step_entry["definition_table"] = datatable
        request.node.bdd_steps_data.append(step_entry)

    if step.type == "then":
        step_entry = {
            "step_name": step.name,
            "type": step.type,
            "results_expected": [],
            "results_actual": [],
        }

        # Creating the expected results dict from the datatable
        # and add in .json
        datatable = step_func_args.get("datatable")
        # A step without datatable still has one result to compare
        row_count = len(datatable) if datatable else 1

        step_entry["step_result"] = "PASS"
        fail_data = None
        for index in range(row_count):
            # Creating the actual results dict and add in .json
            tracker = step_func_args.get("results_tracker")
            expec_res = {tracker[index]["param"]: tracker[index]["expected"]}
            actual_res = {tracker[index]["param"]: tracker[index]["actual"]}
            step_entry["results_expected"].append(expec_res)
            step_entry["results_actual"].append(actual_res)

            # Comparing the actual with the expected value and attribute
            # PASS or FAIL
            # for the specific step (the first failing row is the one reported)
            if tracker[index]["expected"] == tracker[index][
                "actual"
            ] and tracker[index]["compairison"] in ("equal_str", "equal_int"):
                pass
            elif fail_data is None:
                fail_data = {
                    "feature": feature.name,
                    "scenario": scenario.name,
                    "failed_step": f"{step.keyword} {step.name}",
                    "line_number": getattr(step, "line_number", "Unknown"),
                    "failuire": (
                        f"{tracker[index]['param']} was expected to be "
                        "equal to "
                        f"{tracker[index]['expected']}, but is equal to "
                        f"{tracker[index]['actual']}"
                    ),
                }

        if fail_data:
            step_entry["step_result"] = "FAIL"
            step_entry["failuire_data"] = fail_data

        # Adding all the extra step data (expected/actual and step results)
        request.node.bdd_steps_data.append(step_entry)


def pytest_bdd_step_error(request, feature, scenario, step, exception):
    """Identify a BDD step failure.

    Fills the .json file with all the info following an error in the step.
    """
    request.node.bdd_steps_data = []
    error_data = {
        "feature": feature.name,
        "scenario": scenario.name,
        "failed_step": f"{step.keyword} {step.name}",
        "line_number": getattr(step, "line_number", "Unknown"),
        "exception": str(exception),
    }
    step_entry = {"step_name": step.name, "type": step.type}
    step_entry["error_data"] = error_data
    request.node.bdd_steps_data.append(step_entry)


def pytest_bdd_after_scenario(request):
    """Compute the overall scenario result after all steps have executed.

    Sets request.node.bdd_scenario_result to "PASS" if every step passed,
    "FAIL" otherwise.
    """
    if not hasattr(request.node, "bdd_steps_data"):
        return None

    step_results = [
        entry["step_result"]
        for entry in request.node.bdd_steps_data
        if "step_result" in entry
    ]

    # Filling json report finished scenario time
    setattr(request.node, "scenario_finish_time", datetime.now().isoformat())

    # Scenario PASS/FAIL result
    scenario_result = (
        "PASS"
        if step_results and all(r == "PASS" for r in step_results)
        else "FAIL"
    )

    request.node.bdd_scenario_result = scenario_result

    # Will mark the test FAILED if the result is none of these
    assert request.node.bdd_scenario_result in ("PASS", "XPASS")


def pytest_bdd_apply_tag(tag, function):
    """Make sure the skip tag comes with a comment and display it."""
    if tag == "skip":
        logger.warning("Please add a comment to your skip tag")
        return None
    elif tag.startswith("skip_"):
        pattern = r"skip_(.*)"
        match = re.search(pattern, tag)

        if match:
            # Apply the skip marker with your comment/reason
            marker = pytest.mark.skip(reason=match.group(1))
            marker(function)
            return True
        logger.warning(
            'Your skip tag has a syntax problem, must be @skip("message")'
        )
        return None
    else:
        return None


@pytest.hookimpl(optionalhook=True)
def pytest_json_runtest_metadata(item, call):
    """Add custom data to the JSON report.

    Adds bdd_steps_data and other info about the scenario.
    """
    if call.when == "call" and hasattr(item, "bdd_steps_data"):
        return {
            "scenario_id": getattr(item, "bdd_scenario_id", None),
            "scenario_feature": getattr(item, "bdd_feature_name", None),
            "scenario_jenkins_filter": getattr(
                item, "bdd_scenario_filter", None
            ),
            "bdd_steps": item.bdd_steps_data,
            "scenario_result": getattr(item, "bdd_scenario_result", None),
            "scenario_finish_time": getattr(
                item, "scenario_finish_time", None
            ),
        }
