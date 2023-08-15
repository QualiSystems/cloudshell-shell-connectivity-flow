from __future__ import annotations

from abc import abstractmethod
from collections.abc import Collection
from concurrent.futures import ThreadPoolExecutor, wait
from itertools import chain, groupby
from typing import Any

from attrs import define

from cloudshell.shell.flows.connectivity.abstrace_flow import AbcConnectivityFlow
from cloudshell.shell.flows.connectivity.helpers.group_cp_actions import group_actions
from cloudshell.shell.flows.connectivity.models.connectivity_model import (
    ConnectivityActionModel,
    get_vm_uuid,
    get_vnic,
    is_remove_action,
    is_set_action,
)


class AbcCloudProviderConnectivityFlow(AbcConnectivityFlow):
    def _clear_targets(
        self, actions: Collection[ConnectivityActionModel], executor: ThreadPoolExecutor
    ) -> None:
        """Do not clear targets for Cloud Provider."""

    def _rollback_failed_set_actions(
        self,
        set_actions: Collection[Collection[ConnectivityActionModel]],
        executor: ThreadPoolExecutor,
    ) -> None:
        # get failed action ids
        failed_action_ids = set()
        for action_id, results in self.results.items():
            if not all(result.success for result in results):
                failed_action_ids.add(action_id)
                continue

        actions_to_rollback = []
        for action in chain.from_iterable(set_actions):  # type: ConnectivityActionModel
            if action.action_id in failed_action_ids:
                # get all sub action for the failed action id
                actions_to_rollback.append(action)

        # execute clear actions, ignore results
        futures = [
            executor.submit(self.clear, a, self.get_target(a))
            for a in actions_to_rollback
        ]
        wait(futures)

    @abstractmethod
    def get_vnics(self, vm: Any) -> Collection[VnicInfo]:
        raise NotImplementedError

    def vnic_name_to_index(self, name: str, vm: Any) -> str:
        return name.rsplit(" ", 1)[-1]

    def _prepare_remove_actions(
        self, actions: Collection[ConnectivityActionModel]
    ) -> Collection[Collection[ConnectivityActionModel]]:
        remove_actions_groups = [(a,) for a in list(filter(is_remove_action, actions))]
        return remove_actions_groups

    def _prepare_set_actions(
        self, actions: Collection[ConnectivityActionModel]
    ) -> list[tuple[ConnectivityActionModel, ...]]:
        """Prepare set actions for a Cloud Provider.

        Check that we can connect actions to the VM.
        Set vNIC index for each action.
        Return groups of actions:
            existed vNICs in separate groups (one action per group)
            new vNICs in one group in the right order
        """
        set_actions = list(filter(is_set_action, actions))

        actions_by_vm = _group_actions_by_vm(set_actions)
        set_actions_groups: list[tuple[ConnectivityActionModel, ...]] = []
        for vm_uuid, actions in actions_by_vm.items():
            vm = self.get_target(vm_uuid)
            self._replace_vnic_names_with_indexes(actions, vm)
            _validate_not_duplicated_vnics(actions)
            vnics = self.get_vnics(vm)
            new_groups_actions = group_actions(actions, vnics)
            set_actions_groups.extend(new_groups_actions)

        return set_actions_groups

    def _replace_vnic_names_with_indexes(
        self, actions: Collection[ConnectivityActionModel], vm: Any
    ) -> None:
        for action in actions:
            vnic_name = action.custom_action_attrs.vnic
            vnic_index = self.vnic_name_to_index(vnic_name, vm)
            action.custom_action_attrs.vnic = vnic_index


@define
class VnicInfo:
    name: str
    index: int
    network_can_be_replaced: bool


def _group_actions_by_vm(
    actions: Collection[ConnectivityActionModel],
) -> dict[str, list[ConnectivityActionModel]]:
    return {
        vm_uuid: list(grouped_actions)
        for vm_uuid, grouped_actions in groupby(
            sorted(actions, key=get_vm_uuid), key=get_vm_uuid
        )
    }


def _validate_not_duplicated_vnics(
    actions: Collection[ConnectivityActionModel],
) -> None:
    vnics = set()
    for vnic in map(get_vnic, actions):
        if vnic and vnic in vnics:
            raise ValueError(f"Duplicate vNIC {vnic}")
        vnics.add(vnic)
