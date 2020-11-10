from __future__ import annotations

from abc import abstractmethod
from collections import defaultdict
from concurrent import futures as ft
from itertools import groupby
from logging import Logger

from cloudshell.shell.flows.connectivity.models.connectivity_model import (
    ConnectivityActionModel,
    get_actions_from_request,
)
from cloudshell.shell.flows.connectivity.models.driver_response import (
    ConnectivityActionResult,
    DriverResponseRoot,
)


class AbstractConnectivityFlow:
    MODEL = ConnectivityActionModel
    # Indicates if VLAN ranges are supported like "120-130"
    IS_VLAN_RANGE_SUPPORTED = True
    # Indicates if device supports comma separated VLAN request like "45, 65, 120-130"
    IS_MULTI_VLAN_SUPPORTED = True

    def __init__(self, logger: Logger):
        self._logger = logger
        self._success_msgs = defaultdict(list)  # action_id: [msg]
        self._error_msgs = defaultdict(list)  # action_id: [msg]

    @abstractmethod
    def _set_vlan(self, action: ConnectivityActionModel) -> str:
        pass

    @abstractmethod
    def _remove_vlan(self, action: ConnectivityActionModel) -> str:
        pass

    @abstractmethod
    def _remove_all_vlans(self, action: ConnectivityActionModel) -> str:
        pass

    def _get_result(self, actions: list[ConnectivityActionModel]) -> str:
        action_results = []
        for action in actions:
            err_msgs = self._error_msgs.get(action.action_id)
            vlan = action.connection_params.vlan_id
            if err_msgs:
                err_msgs = "\n\t".join(self._error_msgs[action.action_id])
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

    def _group_actions(
        self, actions: list[ConnectivityActionModel]
    ) -> list[ConnectivityActionModel]:
        def key_fn(action):
            return (
                action.action_target.name,
                action.custom_action_attrs.vm_uuid,
                action.custom_action_attrs.vnic,
            )

        return [
            next(grouped_actions)
            for _, grouped_actions in groupby(sorted(actions, key=key_fn), key=key_fn)
        ]

    def _wait_futures(self, futures: dict[ft.Future, ConnectivityActionModel]):
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
        actions = get_actions_from_request(
            request,
            self.MODEL,
            self.IS_VLAN_RANGE_SUPPORTED,
            self.IS_MULTI_VLAN_SUPPORTED,
        )
        set_actions = list(filter(lambda a: a.type is a.type.SET_VLAN, actions))
        remove_actions = list(filter(lambda a: a.type is a.type.REMOVE_VLAN, actions))

        with ft.ThreadPoolExecutor() as executor:
            remove_all_vlan_futures = {
                executor.submit(self._remove_all_vlans, action): action
                for action in self._group_actions(set_actions)
            }
            self._wait_futures(remove_all_vlan_futures)

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
