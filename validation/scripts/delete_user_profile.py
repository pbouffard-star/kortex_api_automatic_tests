#! /usr/bin/env python3
"""Delete a user profile from the arm, if it exists.

Usage: python3.9 delete_user_profile.py <username> [--ip IP] [-u USER] [-p PWD]

Used as a cleanup before checking the output of examples that create a user
profile (ex: the notification example), so that a previous failed run does
not leave the profile on the device.
"""

import argparse
import os
import sys

EXAMPLES_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "..",
    "api_python",
    "examples",
)
sys.path.insert(0, EXAMPLES_PATH)

import utilities  # noqa: E402
from kortex_api.autogen.client_stubs.BaseClientRpc import (  # noqa: E402
    BaseClient,
)


def main():
    """Delete every user profile matching the given username."""
    parser = argparse.ArgumentParser()
    parser.add_argument("target_username", type=str)
    args = utilities.parseConnectionArguments(parser)

    with utilities.DeviceConnection.createTcpConnection(args) as router:
        base = BaseClient(router)
        deleted = 0
        for profile in base.ReadAllUserProfiles().user_profiles:
            if profile.username == args.target_username:
                base.DeleteUserProfile(profile.handle)
                deleted += 1
        print(f"Deleted {deleted} user profile(s) named {args.target_username}")


if __name__ == "__main__":
    main()
