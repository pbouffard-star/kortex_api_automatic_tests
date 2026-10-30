from glob import glob

from pytest_bdd import scenarios
from steps.run_python import *  # noqa: F401,F403

for feature_file in glob('../feature_files/*.feature', recursive=True):
    scenarios(feature_file)
