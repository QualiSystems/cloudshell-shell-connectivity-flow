import logging
from typing import Callable

from .exceptions import ApplyConnectivityException
from .models.connectivity_model import ConnectivityActionModel, ConnectivityTypeEnum
from .models.driver_response import ConnectivityActionResult, DriverResponseRoot
from .parse_request_service import ParseConnectivityRequestService

logger = logging.getLogger(__name__)


def apply_connectivity_changes(
    request: str,
    add_vlan_action: Callable[[ConnectivityActionModel], ConnectivityActionResult],
    remove_vlan_action: Callable[[ConnectivityActionModel], ConnectivityActionResult],
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
    :return Returns a driver action result object,
            this can be returned to CloudShell server by the command result
    """
    if request is None or request == "":
        raise ApplyConnectivityException("Request is None or empty")

    actions = ParseConnectivityRequestService(
        is_vlan_range_supported=True, is_multi_vlan_supported=True
    ).get_actions(request)

    results = []
    for action in actions:
        logger.info(f"Action: {actions}")
        if action.type is ConnectivityTypeEnum.SET_VLAN:
            action_result = add_vlan_action(action)
        else:
            action_result = remove_vlan_action(action)
        results.append(action_result)

    return str(DriverResponseRoot.prepare_response(results).json())
