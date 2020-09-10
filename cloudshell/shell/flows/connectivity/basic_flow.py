import json
from abc import abstractmethod
from collections import defaultdict
from logging import Logger
from threading import Thread
from typing import List, Optional

from cloudshell.shell.flows.connectivity.helpers.vlan_handler import VLANHandler
from cloudshell.shell.flows.connectivity.models.connectivity_model import (
    ConnectionModeEnum,
    ConnectivityActionModel,
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
        self._set_vlan_threads: List[Thread] = []
        self._remove_vlan_threads: List[Thread] = []
        self._success_msgs = defaultdict(list)  # action_id: [msg]
        self._error_msgs = defaultdict(list)  # action_id: [msg]
        self._vlan_helper = VLANHandler(
            self.IS_VLAN_RANGE_SUPPORTED, self.IS_MULTI_VLAN_SUPPORTED
        )
        self._remove_all_vlans_set = set()  # {(target_name, vm_uid)}

    def _get_actions(self, requests: str) -> List[ConnectivityActionModel]:
        dict_actions = json.loads(requests)["driverRequest"]["actions"]
        return [self.MODEL.parse_obj(action) for action in dict_actions]

    @abstractmethod
    def _set_vlan(
        self,
        vlan: str,
        port_mode: ConnectionModeEnum,
        target_name: str,
        qnq: bool,
        ctag: str,
        vm_uid: Optional[str],
    ) -> str:
        pass

    @abstractmethod
    def _remove_vlan(
        self,
        vlan: str,
        port_mode: ConnectionModeEnum,
        target_name: str,
        qnq: bool,
        ctag: str,
        vm_uid: Optional[str],
    ) -> str:
        pass

    @abstractmethod
    def _remove_all_vlans(self, target_name: str, vm_uid: Optional[str] = None):
        pass

    def _add_set_vlan_thread(self, vlan: str, action: ConnectivityActionModel):
        t = Thread(target=self._set_vlan_executor, args=(vlan, action))
        self._set_vlan_threads.append(t)

    def _set_vlan_executor(self, vlan: str, action: ConnectivityActionModel):
        target_name = action.action_target.name
        self._remove_all_vlans_set.add((target_name, action.vm_uid))
        try:
            msg = self._set_vlan(
                vlan,
                action.connection_params.mode,
                target_name,
                action.connection_params.qnq,
                action.connection_params.ctag,
                action.vm_uid,
            )
            self._success_msgs[action.action_id].append(msg)
        except Exception as e:
            emsg = f"Failed to configure vlan {vlan} for target {target_name}"
            if action.vm_uid is not None:
                emsg = f"{emsg} on VM ID {action.vm_uid}"
            self._logger.exception(emsg)
            self._error_msgs[action.action_id].append(str(e))

    def _add_remove_vlan_thread(self, vlan: str, action: ConnectivityActionModel):
        t = Thread(target=self._remove_vlan_executor, args=(vlan, action))
        self._remove_vlan_threads.append(t)

    def _remove_vlan_executor(self, vlan: str, action: ConnectivityActionModel):
        target_name = action.action_target.name
        try:
            msg = self._remove_vlan(
                vlan,
                action.connection_params.mode,
                target_name,
                action.connection_params.qnq,
                action.connection_params.ctag,
                action.vm_uid,
            )
            self._success_msgs[action.action_id].append(msg)
        except Exception as e:
            emsg = f"Failed to configure vlan {vlan} for target {target_name}"
            if action.vm_uid is not None:
                emsg = f"{emsg} on VM ID {action.vm_uid}"
            self._logger.exception(emsg)
            self._error_msgs[action.action_id].append(str(e))

    def _get_result(self, actions: List[ConnectivityActionModel]) -> str:
        action_results = []
        for action in actions:
            err_msgs = self._error_msgs.get(action.action_id)
            if err_msgs:
                err_msgs = "\n\t".join(self._error_msgs[action.action_id])
                msg = (
                    f"Add Vlan {action.connection_params.vlan_id} configuration failed."
                    f"\nAdd Vlan configuration details:\n{err_msgs}"
                )
                result = ConnectivityActionResult.fail_result(action, msg)
            else:
                msg = (
                    f"Add Vlan {action.connection_params.vlan_id} configuration "
                    f"successfully completed"
                )
                result = ConnectivityActionResult.success_result(action, msg)
            action_results.append(result)

        return DriverResponseRoot.prepare_response(action_results).json()

    def apply_connectivity(self, requests: str) -> str:
        actions = self._get_actions(requests)
        for action in actions:
            # todo move vlan validation and parsing into model
            for vlan in self._vlan_helper.get_vlan_list(
                action.connection_params.vlan_id
            ):
                if action.type is action.type.SET_VLAN:
                    self._add_set_vlan_thread(vlan, action)
                else:
                    self._add_remove_vlan_thread(vlan, action)

        for target_name, vm_uid in self._remove_all_vlans_set:
            self._remove_all_vlans(target_name, vm_uid)
        start_and_wait_threads(self._remove_vlan_threads)
        start_and_wait_threads(self._set_vlan_threads)

        return self._get_result(actions)


def start_and_wait_threads(threads: List[Thread]):
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
