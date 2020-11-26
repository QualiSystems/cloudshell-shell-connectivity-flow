from abc import ABC, abstractmethod
from collections import defaultdict
from concurrent import futures as ft
from logging import Logger
from typing import Dict, List

from cloudshell.shell.flows.connectivity.helpers.remove_vlans import (
    prepare_remove_vlan_actions,
)
from cloudshell.shell.flows.connectivity.models.connectivity_model import (
    ConnectivityActionModel,
)
from cloudshell.shell.flows.connectivity.models.driver_response import (
    ConnectivityActionResult,
    DriverResponseRoot,
)
from cloudshell.shell.flows.connectivity.parse_request_service import (
    AbstractParseConnectivityService,
)


class AbstractConnectivityFlow(ABC):
    def __init__(
        self,
        parse_connectivity_request_service: AbstractParseConnectivityService,
        logger: Logger,
    ):
        self._parse_connectivity_request_service = parse_connectivity_request_service
        self._logger = logger
        self._success_msgs = defaultdict(list)  # action_id: [msg]
        self._error_msgs = defaultdict(list)  # action_id: [msg]

    @abstractmethod
    def _set_vlan(self, action: ConnectivityActionModel) -> str:
        raise NotImplementedError()

    @abstractmethod
    def _remove_vlan(self, action: ConnectivityActionModel) -> str:
        """Remove VLAN for the target.

        Target is defined by action_target.name for a port on networking device
        or custom_action_attrs.vm_uuid and custom_action_attrs.vnic for a VM.
        If connection_params.vlan_id is empty you should clear all VLANs for the target.
        """
        raise NotImplementedError()

    def _get_result(self, actions: List[ConnectivityActionModel]) -> str:
        action_results = []
        for action in actions:
            err_msgs = self._error_msgs.get(action.action_id)
            vlan = action.connection_params.vlan_id
            if err_msgs:
                err_msgs = "\n\t".join(err_msgs)
                msg = (
                    f"Vlan {vlan} configuration failed.\n"
                    f"Vlan configuration details:\n{err_msgs}"
                )
                result = ConnectivityActionResult.fail_result(action, msg)
            else:
                msg = f"Vlan {vlan} configuration " f"successfully completed"
                result = ConnectivityActionResult.success_result(action, msg)
            action_results.append(result)

        return DriverResponseRoot.prepare_response(action_results).json()

    def _wait_futures(self, futures: Dict[ft.Future, ConnectivityActionModel]):
        ft.wait(futures)
        for future, action in futures.items():
            try:
                msg = future.result()
            except Exception as e:
                vlan = action.connection_params.vlan_id
                target_name = action.action_target.name
                emsg = f"Failed to apply VLAN changes ({vlan}) for target {target_name}"
                if action.custom_action_attrs.vm_uuid:
                    emsg += f" on VM ID {action.custom_action_attrs.vm_uuid}"
                    if action.custom_action_attrs.vnic:
                        emsg += f" for vNIC {action.custom_action_attrs.vnic}"
                self._logger.exception(emsg)
                self._error_msgs[action.action_id].append(str(e))
            else:
                self._success_msgs[action.action_id].append(msg)

    def apply_connectivity(self, request: str) -> str:
        actions = self._parse_connectivity_request_service.get_actions(request)
        set_actions = list(filter(lambda a: a.type is a.type.SET_VLAN, actions))
        remove_actions = list(filter(lambda a: a.type is a.type.REMOVE_VLAN, actions))
        remove_actions = prepare_remove_vlan_actions(set_actions, remove_actions)

        with ft.ThreadPoolExecutor() as executor:
            remove_vlan_futures = {
                executor.submit(self._remove_vlan, action): action
                for action in remove_actions
            }
            self._wait_futures(remove_vlan_futures)

            set_vlan_futures = {
                executor.submit(self._set_vlan, action): action
                for action in set_actions
            }
            self._wait_futures(set_vlan_futures)

        return self._get_result(actions)
