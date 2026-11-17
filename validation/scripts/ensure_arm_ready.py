#! /usr/bin/env python3
"""Put the arm in the servoing ready state, so the motion examples can run.

Usage: python3.9 ensure_arm_ready.py [--ip IP] [-u USER] [-p PWD]

The arm can be left in another state by a previous run or by someone
(ex: hand-guiding, low level servoing, fault). The faults are cleared and
the single level servoing mode is set, then the arm state is polled until it
is ready. Exit code is 0 when the arm is ready, 1 otherwise.
"""

import os
import sys
import time

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
from kortex_api.autogen.messages import Base_pb2  # noqa: E402

READY = Base_pb2.ARMSTATE_SERVOING_READY
WAIT_SECONDS = 15


def arm_state_name(base):
    """Return the name of the current arm state."""
    return Base_pb2.ArmState.Name(base.GetArmState().active_state)


def main():
    """Bring the arm to ARMSTATE_SERVOING_READY."""
    args = utilities.parseConnectionArguments()
    try:
        with utilities.DeviceConnection.createTcpConnection(args) as router:
            base = BaseClient(router)
            state = arm_state_name(base)
            if state == Base_pb2.ArmState.Name(READY):
                print(f"Arm already ready ({state})")
                return
            print(f"Arm in {state}, setting it back to servoing ready")

            if state == "ARMSTATE_IN_FAULT":
                base.ClearFaults()
            servoing_mode = Base_pb2.ServoingModeInformation()
            servoing_mode.servoing_mode = Base_pb2.SINGLE_LEVEL_SERVOING
            base.SetServoingMode(servoing_mode)

            deadline = time.monotonic() + WAIT_SECONDS
            while time.monotonic() < deadline:
                state = arm_state_name(base)
                if state == Base_pb2.ArmState.Name(READY):
                    print(f"Arm ready ({state})")
                    return
                time.sleep(0.5)
            print(f"Arm still in {state} after {WAIT_SECONDS} seconds")
            sys.exit(1)
    except SystemExit:
        raise
    except Exception as error:
        print(f"Could not set the arm ready: {type(error).__name__} {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
