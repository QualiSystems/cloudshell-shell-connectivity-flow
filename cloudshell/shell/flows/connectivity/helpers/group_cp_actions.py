from __future__ import annotations

from collections.abc import Collection
from itertools import filterfalse
from typing import TYPE_CHECKING

from cloudshell.shell.flows.connectivity.models.connectivity_model import (
    ConnectivityActionModel,
    get_vm_uuid,
    get_vnic,
)

if TYPE_CHECKING:
    from cloudshell.shell.flows.connectivity.cloud_providers_flow import VnicInfo


def group_actions(
    actions: Collection[ConnectivityActionModel], vnics: Collection[VnicInfo]
) -> list[tuple[ConnectivityActionModel, ...]]:
    """Group Cloud Provider's actions.

    Return groups of actions:
        - groups with one action per group for vNICs that exists on a VM
        - one group for all actions that will create new vNICs on a VM in right order -
          from the lowest index to the highest
    """
    # all vNICs should be digit strings or empty string with the same VM UUID
    assert all(v.isdigit() or v == "" for v in map(get_vnic, actions))
    assert len(set(map(get_vm_uuid, actions))) == 1

    last_vnic_index = max(vnic.index for vnic in vnics)
    vnics_to_use = {vnic.index: vnic for vnic in vnics if vnic.network_can_be_replaced}
    actions = sorted(actions, key=_sort_actions_by_vnic)

    actions_to_replace_vnics = []
    actions_to_create_new_vnics = []
    for action in filter(get_vnic, actions):
        vnic = get_vnic(action)
        vnic_index = int(vnic)
        if vnics_to_use.pop(vnic_index, None):
            actions_to_replace_vnics.append(action)
        else:
            if vnic_index > last_vnic_index:
                actions_to_create_new_vnics.append(action)
            else:
                raise ValueError(
                    f"Cannot connect to vNIC {vnic_index} because it is already used"
                )

    for action in filterfalse(get_vnic, actions):
        if vnics_to_use:
            vnic_index = next(iter(vnics_to_use))  # get first index
            vnics_to_use.pop(vnic_index)
            action.custom_action_attrs.vnic = str(vnic_index)
            actions_to_replace_vnics.append(action)
        else:
            prev_used_index = last_vnic_index
            for i, another_action in enumerate(actions_to_create_new_vnics):
                action_vnic_index = int(get_vnic(another_action))
                if action_vnic_index == prev_used_index + 1:
                    prev_used_index += 1
                    continue
                else:
                    # inserting action before prev_action
                    action.custom_action_attrs.vnic = str(prev_used_index + 1)
                    actions_to_create_new_vnics.insert(i, action)
                    break
            else:
                # inserting action at the end
                action.custom_action_attrs.vnic = str(prev_used_index + 1)
                actions_to_create_new_vnics.append(action)

    prev_index = last_vnic_index
    for action in actions_to_create_new_vnics:
        vnic_index = int(get_vnic(action))
        if vnic_index != prev_index + 1:
            raise ValueError(
                "There are gaps between vNIC indexes that should be created"
            )
        prev_index = vnic_index

    groups_actions: list[tuple[ConnectivityActionModel, ...]] = [
        (a,) for a in actions_to_replace_vnics
    ]
    if actions_to_create_new_vnics:
        groups_actions.append(tuple(actions_to_create_new_vnics))

    return groups_actions


def _sort_actions_by_vnic(action: ConnectivityActionModel) -> tuple[int, int]:
    """Sort actions by vNIC index.

    First actions with vNIC specified in increasing order, then actions without
    vNIC specified.
    """
    if str_vnic := get_vnic(action):
        result = (0, int(str_vnic))
    else:
        result = (1, 0)
    return result
