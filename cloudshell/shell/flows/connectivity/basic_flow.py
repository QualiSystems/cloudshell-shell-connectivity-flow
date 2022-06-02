from __future__ import annotations

from abc import ABC, abstractmethod
from concurrent import futures as ft
from logging import Logger

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
        self._results: dict[str, ConnectivityActionResult] = {}

    @abstractmethod
    def _set_vlan(self, action: ConnectivityActionModel) -> ConnectivityActionResult:
        raise NotImplementedError()

    @abstractmethod
    def _remove_vlan(self, action: ConnectivityActionModel) -> ConnectivityActionResult:
        """Remove VLAN for the target.

        Target is defined by action_target.name for a port on networking device
        or custom_action_attrs.vm_uuid and custom_action_attrs.vnic for a VM.
        If connection_params.vlan_id is empty you should clear all VLANs for the target.
        """
        raise NotImplementedError()

    def _get_result(self) -> str:
        return DriverResponseRoot.prepare_response(list(self._results.values())).json()

    def _wait_futures(self, futures: dict[ft.Future, ConnectivityActionModel]):
        ft.wait(futures)
        for future, action in futures.items():
            try:
                result: ConnectivityActionResult = future.result()
            except Exception as e:
                vlan = action.connection_params.vlan_id
                target_name = action.action_target.name
                emsg = f"Failed to apply VLAN changes ({vlan}) for target {target_name}"
                if action.custom_action_attrs.vm_uuid:
                    emsg += f" on VM ID {action.custom_action_attrs.vm_uuid}"
                    if action.custom_action_attrs.vnic:
                        emsg += f" for vNIC {action.custom_action_attrs.vnic}"
                emsg = f"{emsg}. Error: {e}"
                self._logger.exception(emsg)
                result = ConnectivityActionResult.fail_result(action, emsg)
            self._results[result.actionId] = result

    def apply_connectivity(self, request: str) -> str:
        self._logger.debug(f"Apply connectivity request: {request}")
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

            self._filter_set_actions(set_actions)
            set_vlan_futures = {
                executor.submit(self._set_vlan, action): action
                for action in set_actions
            }
            self._wait_futures(set_vlan_futures)

        return self._get_result()

    def _filter_set_actions(self, set_actions: list[ConnectivityActionModel]):
        for action in set_actions[:]:
            result = self._results.get(action.action_id)
            if result and result.success is False:
                set_actions.remove(action)
