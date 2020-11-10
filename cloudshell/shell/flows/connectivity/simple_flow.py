from __future__ import annotations

import logging
from collections.abc import Callable
from logging import Logger
from typing import Optional

from cloudshell.shell.flows.connectivity.exceptions import ApplyConnectivityException
from cloudshell.shell.flows.connectivity.models.connectivity_model import (
    ConnectivityActionModel,
    get_actions_from_request,
)
from cloudshell.shell.flows.connectivity.models.driver_response import (
    ConnectivityActionResult,
    DriverResponseRoot,
)


def apply_connectivity_changes(
    request: str,
    add_vlan_action: Callable[[ConnectivityActionModel], ConnectivityActionResult],
    remove_vlan_action: Callable[[ConnectivityActionModel], ConnectivityActionResult],
    logger: Optional[Logger] = None,
) -> str:
    """Standard implementation for the apply_connectivity_changes operation.

    This function will accept as an input the actions to perform for add/remove vlan.
    It implements the basic flow of decoding the JSON connectivity changes requests,
    and combining the results of the add/remove vlan functions into a result object.

    :param str request: json string sent from the CloudShell server
            describing the connectivity changes to perform
    :param Function -> ConnectivityActionResult remove_vlan_action:
            This action will be called for VLAN remove operations
    :param Function -> ConnectivityActionResult add_vlan_action:
            This action will be called for VLAN add operations
    :param logger: logger to use for the operation, if you don't provide a logger,
            a default Python logger will be used
    :return Returns a driver action result object,
            this can be returned to CloudShell server by the command result
    """
    if not logger:
        logger = logging.getLogger("apply_connectivity_changes")

    if request is None or request == "":
        raise ApplyConnectivityException("Request is None or empty")

    actions = get_actions_from_request(
        request,
        ConnectivityActionModel,
        is_vlan_range_supported=True,
        is_multi_vlan_supported=True,
    )

    results = []
    for action in actions:
        logger.info(f"Action: {actions}")
        if action.type is action.type.SET_VLAN:
            action_result = add_vlan_action(action)
        else:
            action_result = remove_vlan_action(action)
        results.append(action_result)

    return DriverResponseRoot.prepare_response(results).json()
