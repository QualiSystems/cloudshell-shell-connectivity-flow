from __future__ import annotations

import logging
from abc import abstractmethod
from collections import defaultdict
from collections.abc import Callable, Collection
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from itertools import chain
from threading import Lock
from typing import Any

from attrs import define, field

from cloudshell.logging.context_filters import pass_log_context  # type: ignore

from cloudshell.shell.flows.connectivity.models.connectivity_model import (
    ConnectivityActionModel,
    ConnectivityTypeEnum,
    get_vm_uuid_or_target,
)
from cloudshell.shell.flows.connectivity.models.driver_response import (
    ConnectivityActionResult,
    DriverResponseRoot,
)
from cloudshell.shell.flows.connectivity.parse_request_service import (
    AbstractParseConnectivityService,
)

logger = logging.getLogger(__name__)


@define
class AbcConnectivityFlow:
    _parse_connectivity_request_service: AbstractParseConnectivityService
    results: dict[str, list[ConnectivityActionResult]] = field(
        init=False, factory=lambda: defaultdict(list)
    )
    _targets_map: dict[str, Any] = field(init=False, factory=dict)
    _get_target_lock: Lock = field(init=False, factory=Lock)

    def apply_connectivity(self, request: str) -> str:
        logger.debug(f"Apply connectivity request: {request}")
        actions = self.parse_request(request)
        self.validate_actions(actions)

        with ThreadPoolExecutor(initializer=pass_log_context()) as executor:
            remove_actions = self._prepare_remove_actions(actions)
            executor.map(self.remove_vlans, remove_actions)

            set_actions = self._prepare_set_actions(actions)
            executor.map(self.set_vlans, set_actions)
            self._rollback_failed_set_actions(set_actions, executor)

        result = self._get_result()
        logger.debug(f"Connectivity result: {result}")
        return result

    def parse_request(self, request: str) -> list[ConnectivityActionModel]:
        """Parse request and return list of actions.

        Split VLANs on different actions based on a configuration.
        Split VMs vNICs on different actions.
        """
        actions = self._parse_connectivity_request_service.get_actions(request)
        return actions

    def validate_actions(self, actions: Collection[ConnectivityActionModel]) -> None:
        pass

    def set_vlans(self, actions: Collection[ConnectivityActionModel]) -> None:
        """Set VLANs for the sequence of actions."""
        self._execute_actions(self.set_vlan, actions)

    def remove_vlans(self, actions: Collection[ConnectivityActionModel]) -> None:
        """Remove VLANs for the sequence of actions."""
        self._execute_actions(self.remove_vlan, actions)

    @abstractmethod
    def set_vlan(
        self, action: ConnectivityActionModel, target: Any
    ) -> ConnectivityActionResult:
        raise NotImplementedError()

    @abstractmethod
    def remove_vlan(
        self, action: ConnectivityActionModel, target: Any
    ) -> ConnectivityActionResult:
        """Remove VLAN for the target.

        If VLAN is empty all VLANs should be cleared.
        """
        raise NotImplementedError()

    def load_target(self, target_name: str) -> Any:
        return None

    def get_target(self, target_name: str) -> Any:
        with self._get_target_lock:
            try:
                target = self._targets_map[target_name]
            except KeyError:
                target = self.load_target(target_name)
                self._targets_map[target_name] = target
        return target

    def _execute_actions(
        self,
        fn: Callable[[ConnectivityActionModel, Any], ConnectivityActionResult],
        actions: Collection[ConnectivityActionModel],
    ) -> None:
        action_targets = {action.action_target.name for action in actions}
        action_vm_uuids = {action.custom_action_attrs.vm_uuid for action in actions}
        assert len(action_targets) == 1 and len(action_vm_uuids) in (1, 0)

        failed_action = None
        for action in actions:
            if failed_action:
                logger.debug(f"Skip action {action} due to previous failure")
                result = ConnectivityActionResult.skip_result(action)
            else:
                target = self.get_target(get_vm_uuid_or_target(action))
                try:
                    result = fn(action, target)
                except Exception as e:
                    emsg = _get_response_emsg(action, e)
                    logger.exception(emsg)
                    result = ConnectivityActionResult.fail_result(action, emsg)
                    failed_action = action

            self.results[result.actionId].append(result)

    def _rollback_failed_set_actions(
        self,
        set_actions: Collection[Collection[ConnectivityActionModel]],
        executor: ThreadPoolExecutor,
    ) -> None:
        """Rollback all sub actions if one of them failed."""
        # get failed action ids
        failed_action_ids = set()
        for action_id, results in self.results.items():
            for result in results:
                if not result.success and result.type == "setVlan":
                    failed_action_ids.add(action_id)
                    break

        # create remove actions with VLAN = None
        new_remove_actions = []
        for action in chain.from_iterable(set_actions):  # type: ConnectivityActionModel
            if action.action_id in failed_action_ids:
                new_action: ConnectivityActionModel = deepcopy(action)
                new_action.connection_params.vlan_id = ""
                new_action.connection_params.vlan_service_attrs.vlan_id = ""
                new_action.type = ConnectivityTypeEnum.REMOVE_VLAN

                if new_action not in new_remove_actions:
                    # add action as sequence of one action
                    # they will be executed in parallel
                    new_remove_actions.append((action,))

        # execute remove actions
        executor.map(self.remove_vlans, new_remove_actions)

    @abstractmethod
    def _prepare_remove_actions(
        self, actions: Collection[ConnectivityActionModel]
    ) -> Collection[Collection[ConnectivityActionModel]]:
        """Prepare remove actions.

        Return list of actions in groups.
        Groups of actions will be executed in parallel.
        Actions in group will be executed in sequence.
        """
        raise NotImplementedError()

    @abstractmethod
    def _prepare_set_actions(
        self, actions: Collection[ConnectivityActionModel]
    ) -> Collection[Collection[ConnectivityActionModel]]:
        """Prepare set actions.

        Return list of actions in groups.
        Groups of actions will be executed in parallel.
        Actions in group will be executed in sequence.
        """
        raise NotImplementedError()

    def _get_result(self) -> str:
        single_results: dict[str, ConnectivityActionResult] = {}
        for action_id, results in self.results.items():
            for result in results:
                if existed_result := single_results.get(action_id):
                    existed_result.success = existed_result.success and result.success
                    existed_result.infoMessage = (
                        f"{existed_result.infoMessage}\n{result.infoMessage}"
                    )
                    existed_result.errorMessage = (
                        f"{existed_result.errorMessage}\n{result.errorMessage}"
                    )
                    ifaces = set(existed_result.updatedInterface.split(";"))
                    if result.updatedInterface not in ifaces:
                        ifaces.add(result.updatedInterface)
                    existed_result.updatedInterface = ";".join(ifaces)
                else:
                    single_results[action_id] = result

        return str(
            DriverResponseRoot.prepare_response(list(single_results.values())).json()
        )


def _get_response_emsg(action: ConnectivityActionModel, e: Exception) -> str:
    vlan = action.connection_params.vlan_id
    target_name = action.action_target.name
    emsg = f"Failed to apply VLAN changes ({vlan}) for target {target_name}"
    if action.custom_action_attrs.vm_uuid:
        emsg += f" on VM ID {action.custom_action_attrs.vm_uuid}"
        if action.custom_action_attrs.vnic:
            emsg += f" for vNIC {action.custom_action_attrs.vnic}"
    emsg = f"{emsg}. Error: {e}"
    return emsg
