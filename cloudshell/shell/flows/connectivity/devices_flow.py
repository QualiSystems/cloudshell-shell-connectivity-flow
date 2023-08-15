from __future__ import annotations

from abc import ABC
from collections.abc import Collection
from concurrent.futures import ThreadPoolExecutor, wait
from itertools import chain

from .abstrace_flow import AbcConnectivityFlow
from .models.connectivity_model import (
    ConnectivityActionModel,
    ConnectivityTypeEnum,
    is_remove_action,
    is_set_action,
)


class AbcDeviceConnectivityFlow(AbcConnectivityFlow, ABC):
    def _prepare_remove_actions(
        self, actions: Collection[ConnectivityActionModel]
    ) -> Collection[Collection[ConnectivityActionModel]]:
        remove_actions_groups = [(a,) for a in actions if is_remove_action(a)]
        return remove_actions_groups

    def _prepare_set_actions(
        self, actions: Collection[ConnectivityActionModel]
    ) -> Collection[Collection[ConnectivityActionModel]]:
        # get failed actions
        failed_action_ids = {
            result.actionId
            for result in chain.from_iterable(self.results.values())
            if not result.success
        }

        # do not add failed actions to the set actions
        set_actions_groups = [
            (a,)
            for a in actions
            if is_set_action(a) and a.action_id not in failed_action_ids
        ]
        return set_actions_groups

    def _clear_targets(
        self, actions: Collection[ConnectivityActionModel], executor: ThreadPoolExecutor
    ) -> None:
        """Remove all VLANs for the targets."""
        # get one set action per action id
        actions_map = {
            action.action_id: action
            for action in actions
            if action.type is ConnectivityTypeEnum.SET_VLAN
        }

        futures = [
            executor.submit(self._execute_actions, self.clear, (a,))
            for a in actions_map.values()
        ]
        wait(futures)

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
                actions_to_rollback.append(action)
                # get only one sub action per action id
                failed_action_ids.remove(action.action_id)

        # execute clear actions, ignore results
        futures = [
            executor.submit(self.clear, a, self.get_target(a))
            for a in actions_to_rollback
        ]
        wait(futures)
