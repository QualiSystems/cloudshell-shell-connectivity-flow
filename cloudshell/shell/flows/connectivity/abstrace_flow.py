from __future__ import annotations

import logging
from abc import abstractmethod
from collections import defaultdict
from collections.abc import Callable, Collection
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import Any

from attrs import define, field

from cloudshell.logging.context_filters import pass_log_context  # type: ignore

from cloudshell.shell.flows.connectivity.models.connectivity_model import (
    ConnectivityActionModel,
    get_vm_uuid,
    get_vm_uuid_or_target,
    get_vnic,
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
            try:
                self.pre_connectivity(actions, executor)
                self._clear_targets(actions, executor)
                remove_actions = self._prepare_remove_actions(actions)
                tuple(executor.map(self.remove_vlans, remove_actions))

                set_actions = self._prepare_set_actions(actions)
                tuple(executor.map(self.set_vlans, set_actions))
                self._rollback_failed_set_actions(set_actions, executor)
            finally:
                self.post_connectivity(actions, executor)

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

    def pre_connectivity(
        self, actions: Collection[ConnectivityActionModel], executor: ThreadPoolExecutor
    ) -> None:
        """Executes before set/remove VLAN actions."""
        pass

    def set_vlans(self, actions: Collection[ConnectivityActionModel]) -> None:
        """Set VLANs for the sequence of actions."""
        self._execute_actions(self.set_vlan, actions)

    def remove_vlans(self, actions: Collection[ConnectivityActionModel]) -> None:
        """Remove VLANs for the sequence of actions."""
        self._execute_actions(self.remove_vlan, actions)

    @abstractmethod
    def clear(self, action: ConnectivityActionModel, target: Any) -> str:
        """Executes before set VLAN actions or for rolling back failed.

        Returns updated interface if it's different from target name.
        """
        raise NotImplementedError

    @abstractmethod
    def set_vlan(self, action: ConnectivityActionModel, target: Any) -> str:
        """Execute set VLAN action for the target.

        Returns updated interface if it's different from target name.
        """
        raise NotImplementedError()

    @abstractmethod
    def remove_vlan(self, action: ConnectivityActionModel, target: Any) -> str:
        """Remove VLAN for the target.

        Returns updated interface if it's different from target name.
        """
        raise NotImplementedError()

    def post_connectivity(
        self, actions: Collection[ConnectivityActionModel], executor: ThreadPoolExecutor
    ) -> None:
        """Executes after set/remove VLAN actions."""
        pass

    def load_target(self, target_name: str) -> Any:
        return None

    def get_target(self, target_name_or_action: str | ConnectivityActionModel) -> Any:
        if isinstance(target_name_or_action, ConnectivityActionModel):
            target_name = get_vm_uuid_or_target(target_name_or_action)
        else:
            target_name = target_name_or_action

        with self._get_target_lock:
            try:
                target = self._targets_map[target_name]
            except KeyError:
                target = self.load_target(target_name)
                self._targets_map[target_name] = target
        return target

    def _execute_actions(
        self,
        fn: Callable[[ConnectivityActionModel, Any], str],
        actions: Collection[ConnectivityActionModel],
    ) -> None:
        """Execute actions sequentially and save results."""
        action_targets = {action.action_target.name for action in actions}
        action_vm_uuids = {action.custom_action_attrs.vm_uuid for action in actions}
        assert len(action_targets) == 1 and len(action_vm_uuids) in (1, 0)

        failed_action = None
        for action in actions:
            if failed_action:
                logger.debug(f"Skip action {action} due to previous failure")
                result = ConnectivityActionResult.skip_result(action)
            else:
                target = self.get_target(action)
                try:
                    iface = fn(action, target)
                except Exception as e:
                    emsg = _get_response_emsg(action, e)
                    logger.exception(emsg)
                    result = ConnectivityActionResult.fail_result(action, emsg)
                    failed_action = action
                else:
                    result = ConnectivityActionResult.success_result(
                        action, iface=iface
                    )

            self.results[result.actionId].append(result)

    @abstractmethod
    def _rollback_failed_set_actions(
        self,
        set_actions: Collection[Collection[ConnectivityActionModel]],
        executor: ThreadPoolExecutor,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def _clear_targets(
        self, actions: Collection[ConnectivityActionModel], executor: ThreadPoolExecutor
    ) -> None:
        """Remove all VLANs for the targets."""
        raise NotImplementedError

    @abstractmethod
    def _prepare_remove_actions(
        self, actions: Collection[ConnectivityActionModel]
    ) -> Collection[Collection[ConnectivityActionModel]]:
        """Prepare remove actions.

        Return list of actions in groups.
        Groups of actions will be executed in parallel.
        Actions in group will be executed in sequence.
        """
        raise NotImplementedError

    @abstractmethod
    def _prepare_set_actions(
        self, actions: Collection[ConnectivityActionModel]
    ) -> Collection[Collection[ConnectivityActionModel]]:
        """Prepare set actions.

        Return list of actions in groups.
        Groups of actions will be executed in parallel.
        Actions in group will be executed in sequence.
        """
        raise NotImplementedError

    def _get_result(self) -> str:
        single_results: dict[str, ConnectivityActionResult] = {}
        for action_id, results in self.results.items():
            for result in results:
                if existed_result := single_results.get(action_id):
                    _merge_results(existed_result, result)
                else:
                    single_results[action_id] = result

        return str(
            DriverResponseRoot.prepare_response(list(single_results.values())).json()
        )


def _merge_results(ex: ConnectivityActionResult, new: ConnectivityActionResult) -> None:
    ex.success = ex.success and new.success
    if ex.success:
        ex.infoMessage = _merge_result_messages(ex.infoMessage, new.infoMessage)
    else:
        ex.infoMessage = ""  # clear info message if any of actions failed

    ex.errorMessage = _merge_result_messages(ex.errorMessage, new.errorMessage)
    ex.updatedInterface = _merge_ifaces(ex.updatedInterface, new.updatedInterface)


def _merge_result_messages(ex: str, new: str) -> str:
    messages = set(ex.split("\n"))
    messages.add(new)
    return "\n".join(filter(bool, messages))


def _merge_ifaces(ex: str, new: str) -> str:
    ifaces = set(ex.split(";"))
    ifaces.add(new)
    return ";".join(filter(bool, ifaces))


def _get_response_emsg(action: ConnectivityActionModel, e: Exception) -> str:
    vlan = action.connection_params.vlan_id
    target_name = action.action_target.name
    type_ = action.type.value
    emsg = f"Failed to {type_} {vlan} for {target_name}"
    if vm_uuid := get_vm_uuid(action):
        emsg += f" on VM ID {vm_uuid}"
        if vnic := get_vnic(action):
            emsg += f" for vNIC {vnic}"
    emsg = f"{emsg}. Error: {e}"
    return emsg
