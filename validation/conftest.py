#! /usr/bin/python3
''' Conftest file for global Pytest '''

import logging
import os
import re
import sys
from datetime import datetime

import pytest

logger = logging.getLogger(__name__)

# Add templatedProjects/ to sys.path so that python.tests.utils.* imports resolve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TrackerList(list):
    '''A list that auto-creates tracker dicts on index access, removing the need to pre-size.'''
    _template = {"param": None, "expected": None, "actual": None, "compairison": 'equal_str',
                 "step_result": None, "associated_bug": None}

    def __getitem__(self, index):
        while len(self) <= index:
            self.append(self._template.copy())
        return super().__getitem__(index)


@pytest.fixture
def results_tracker():
    '''
    Creates a dictionary list to hold our comparison data in order to determine PASS or FAIL.
    Entries are created on demand when accessed by index.
    '''
    return TrackerList()


def pytest_bdd_before_scenario(request, feature, scenario):
    '''
    Returns the corresponding ID for each scenario, taking account of the scanario outlines
    Returns the corresponding Jenkins filter parameter for each scenario
    '''
    jenkins_filter = 'daily'  # daily is the default

    # Is this a Scenario Outline ?
    template = getattr(request.node.function, '__scenario__', None)
    is_outline = template is not None and template.templated
    callspec = getattr(request.node, 'callspec', None)
    loop_index = next(iter(callspec.indices.values()), 0) if callspec else 0

    for tag in sorted(scenario.tags):
        if tag in ('daily', 'weekly'):
            jenkins_filter = tag

    request.node.bdd_scenario_filter = jenkins_filter
    request.node.bdd_feature_name = feature.name


def pytest_bdd_after_step(request, step, step_func_args, feature, scenario):
    """
    Hook called after each BDD step.
    Fills the .json file with all the info (param, expected, actual, result) for each single step.
    Takes account of the datatable if any.
    """
    if not hasattr(request.node, 'bdd_steps_data'):
        request.node.bdd_steps_data = []

    if step.type in ('when', 'given'):
        # Creating the step definition table dict and add in .json
        step_entry = {"step_name": step.name, "type": step.type}
        datatable = step_func_args.get('datatable')
        if datatable:
            step_entry["definition_table"] = datatable
        request.node.bdd_steps_data.append(step_entry)

    if step.type == 'then':
        step_entry = {"step_name": step.name,
                      "type": step.type,
                      "results_expected": [],
                      "results_actual": []}

        # Creating the expected results dict from the datatable and add in .json
        datatable = step_func_args.get('datatable')
        # to fix for datatable
        if not datatable:
            datatable = [0] * 2  # forcing a lenght of 2 for the datatable

        for index in range(len(datatable) - 1):
            # Creating the actual results dict and add in .json
            tracker = step_func_args.get('results_tracker')
            expec_res = {tracker[index]["param"]: tracker[index]["expected"]}
            actual_res = {tracker[index]["param"]: tracker[index]["actual"]}
            step_entry["results_expected"].append(expec_res)
            step_entry["results_actual"].append(actual_res)

            step_entry["step_result"] = "PASS"

            # Comparing the actual with the expected value and attribute PASS or FAIL
            # for the specific step
            fail_data = None
            if tracker[index]["expected"] == tracker[index]["actual"] and tracker[index]["compairison"] in ("equal_str", "equal_int"):
                pass
            else:
                fail_data = {
                    "feature": feature.name,
                    "scenario": scenario.name,
                    "failed_step": f"{step.keyword} {step.name}",
                    "line_number": getattr(step, 'line_number', 'Unknown'),
                    "failuire": (
                        f'{tracker[index]["param"]} was expected to be equal to '
                        f'{tracker[index]["expected"]}, but is equal to '
                        f'{tracker[index]["actual"]}'
                    )
                }

        if fail_data:
            step_entry["step_result"] = "FAIL"
            step_entry["failuire_data"] = fail_data

        # Adding all the extra step data (expected/actual and step results)
        request.node.bdd_steps_data.append(step_entry)


def pytest_bdd_step_error(request, feature, scenario, step, exception):
    '''
    BDD step failuire idenfication
    Fills the .json file with all the info following an error in the step
    '''
    request.node.bdd_steps_data = []
    error_data = {
        "feature": feature.name,
        "scenario": scenario.name,
        "failed_step": f"{step.keyword} {step.name}",
        "line_number": getattr(step, 'line_number', 'Unknown'),
        "exception": str(exception)
    }
    step_entry = {"step_name": step.name, "type": step.type}
    step_entry["error_data"] = error_data
    request.node.bdd_steps_data.append(step_entry)


def pytest_bdd_after_scenario(request):
    '''
    Computes the overall scenario result after all steps have executed.
    Sets request.node.bdd_scenario_result to "PASS" if every step passed, "FAIL" otherwise.
    '''
    if not hasattr(request.node, 'bdd_steps_data'):
        return None

    step_results = [
        entry["step_result"]
        for entry in request.node.bdd_steps_data
        if "step_result" in entry
    ]

    # Filling json report finished scenario time
    setattr(request.node, "scenario_finish_time", datetime.now().isoformat())

    # Scenario PASS/FAIL result
    scenario_result = "PASS" if step_results and all(r == "PASS" for r in step_results) else "FAIL"

    request.node.bdd_scenario_result = scenario_result

    # Will mark the test FAILED if the result is none of these
    assert request.node.bdd_scenario_result in ("PASS", "XPASS")


def pytest_bdd_apply_tag(tag, function):
    """
    Making sure the skip tag comes with a comment and displays the comment
    """
    if tag == "skip":
        logger.warning("Please add a comment to your skip tag")
        return None
    elif tag.startswith("skip_"):
        pattern = r'skip_(.*)'
        match = re.search(pattern, tag)

        if match:
            # Apply the skip marker with your comment/reason
            marker = pytest.mark.skip(reason=match.group(1))
            marker(function)
            return True
        logger.warning('Your skip tag has a syntax problem, must be @skip("message")')
        return None
    else:
        return None


@pytest.hookimpl(optionalhook=True)
def pytest_json_runtest_metadata(item, call):
    """
    Hook to add custom data to the JSON report by adding bdd_steps_data and other info about the
    scenario
    """
    if call.when == 'call' and hasattr(item, 'bdd_steps_data'):
        return {
            'scenario_id': getattr(item, 'bdd_scenario_id', None),
            'scenario_feature': getattr(item, 'bdd_feature_name', None),
            'scenario_jenkins_filter': getattr(item, 'bdd_scenario_filter', None),
            'bdd_steps': item.bdd_steps_data,
            'scenario_result': getattr(item, 'bdd_scenario_result', None),
            'scenario_finish_time': getattr(item, 'scenario_finish_time', None),
        }
