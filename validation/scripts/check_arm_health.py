#! /usr/bin/env python3
"""Check that every device of the arm answers to a request.

Usage: python3.9 check_arm_health.py [--ip IP] [-u USER] [-p PWD]

Exit code is 0 when all the devices answer, 1 otherwise. The unresponsive
devices are listed on the output.
"""

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
from kortex_api.autogen.client_stubs.DeviceConfigClientRpc import (  # noqa: E402
    DeviceConfigClient,
)
from kortex_api.autogen.client_stubs.DeviceManagerClientRpc import (  # noqa: E402
    DeviceManagerClient,
)
from kortex_api.autogen.messages import Common_pb2  # noqa: E402
from kortex_api.RouterClient import RouterClientSendOptions  # noqa: E402

REQUEST_TIMEOUT_MS = 3000


def main():
    """List the devices and ask each of them for its type."""
    args = utilities.parseConnectionArguments()
    options = RouterClientSendOptions()
    options.timeout_ms = REQUEST_TIMEOUT_MS

    unresponsive = []
    try:
        with utilities.DeviceConnection.createTcpConnection(args) as router:
            device_manager = DeviceManagerClient(router)
            device_config = DeviceConfigClient(router)
            devices = device_manager.ReadAllDevices(0, options).device_handle
            for device in devices:
                name = Common_pb2.DeviceTypes.Name(device.device_type)
                try:
                    device_config.GetDeviceType(
                        device.device_identifier, options
                    )
                except Exception as error:
                    unresponsive.append(
                        f"{name} (id {device.device_identifier}): "
                        f"{type(error).__name__} {error}".rstrip()
                    )
    except Exception as error:
        print(f"Arm not reachable: {error}")
        sys.exit(1)

    if unresponsive:
        print("Unresponsive device(s): " + "; ".join(unresponsive))
        sys.exit(1)
    print(f"All {len(devices)} device(s) answer")


if __name__ == "__main__":
    main()
