from __future__ import annotations

from abc import ABC
from itertools import chain
from typing import Any, Collection

from cloudshell.shell.flows.connectivity.abstrace_flow import AbcConnectivityFlow
from cloudshell.shell.flows.connectivity.helpers.remove_vlans import (
    prepare_remove_vlan_actions,
)
from cloudshell.shell.flows.connectivity.models.connectivity_model import (
    ConnectivityActionModel,
    is_remove_action,
    is_set_action,
)


class AbcDeviceConnectivityFlow(AbcConnectivityFlow, ABC):
    def _prepare_remove_actions(
        self, actions: list[ConnectivityActionModel]
    ) -> Collection[Collection[ConnectivityActionModel], Any]:
        set_actions = list(filter(is_set_action, actions))
        remove_actions = list(filter(is_remove_action, actions))
        # add remove actions for cleaning all VLANs on the port
        remove_actions_groups = [
            (a,) for a in prepare_remove_vlan_actions(set_actions, remove_actions)
        ]
        return remove_actions_groups

    def _prepare_set_actions(
        self, actions: list[ConnectivityActionModel]
    ) -> Collection[Collection[ConnectivityActionModel], Any]:
        # get failed actions
        failed_action_ids = {
            result.actionId
            for result in chain.from_iterable(self.results.values())
            if not result.success
        }

        set_actions = list(filter(is_set_action, actions))
        # do not add failed actions to the set actions
        set_actions_groups = [
            (a,) for a in set_actions if a.action_id not in failed_action_ids
        ]
        return set_actions_groups
