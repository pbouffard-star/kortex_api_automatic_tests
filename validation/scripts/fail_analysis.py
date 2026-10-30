''' This script will analyse the failuires vs the associated bug '''
import json
import sys


def find_unanalysed_fails(output_file: str):
    '''
    Finds all the unanalysed failuires

    Has to be analysed ASAP if the test is wrong or a bug has to be raised

    *Args*:
        output_file (str): the output file to read
    '''
    unanalysed_fails = []

    with open(output_file, encoding='utf8') as file:
        report = json.load(file)

    for test in report.get('tests', []):
        scen_result = test.get('metadata', {}).get('scenario_result', None)
        if scen_result == "FAIL":
            scen_id = test.get('metadata', {}).get('scenario_id', None)
            scen_name = test.get('nodeid', None).replace('scenarios.py::test_', '')
            unanalysed_fails.append(f'{scen_id} - {scen_name}')

    if len(unanalysed_fails) != 0:
        print('!!! The following scenario(s) fail(s) without any bug associated to them.')
        print('Please analyse them, debug and raise a bug if needed !!!')
        for failuire in unanalysed_fails:
            print(failuire)
        # This will raise a failuire in Jenkins
        sys.exit(1)


def find_unexpected_pass(output_file: str):
    '''
    Finds all the unexpected PASS tests (XPASS in pytest)

    Those tests are associated to a bug, but indicate PASS in the latest Test 
    Run
    2 possibilities:
     - The bug is intermittant (no action required)
     - The bug is fix, but has not been removed from the .feature file

    *Args*:
        output_file (str): the output file to read
    '''
    unexpected_pass = []

    with open(output_file, encoding='utf8') as file:
        report = json.load(file)

    for test in report.get('tests', []):
        scen_result = test.get('metadata', {}).get('scenario_result', None)
        if scen_result == "XPASS":
            scen_id = test.get('metadata', {}).get('scenario_id', None)
            scen_name = test.get('nodeid', None).replace('scenarios.py::test_', '')
            unexpected_pass.append(f'{scen_id} - {scen_name}')

    if len(unexpected_pass) != 0:
        print('The following scenario(s) are associated to a bug, but indicate PASS in the latest Test Run.')
        print('Please analyse them and remove the bug(s) if needed')
        for x_pass in unexpected_pass:
            print(x_pass)
        # This will raise a warning in Jenkins
        sys.exit(2)


def main():
    if len(sys.argv) > 1:
        print(f"Output file: {sys.argv[1]}")
    else:
        print("No output file provided.")

    find_unanalysed_fails(sys.argv[1])
    find_unexpected_pass(sys.argv[1])


if __name__ == "__main__":
    main()
