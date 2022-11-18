from __future__ import annotations

import re
from copy import deepcopy

from cloudshell.shell.flows.connectivity.exceptions import ConnectivityException
from cloudshell.shell.flows.connectivity.helpers.dict_action_helpers import (
    get_val_from_list_attrs,
    set_val_to_list_attrs,
)

VNIC_NAME = "Vnic Name"
VM_UUID = "VM_UUID"


def get_custom_action_attrs(dict_action: dict) -> list[dict[str, str]]:
    return dict_action["customActionAttributes"]


def iterate_dict_actions_by_requested_vnic(dict_action: dict):
    """Iterates over dict actions by requested vNIC."""
    custom_action_attrs = get_custom_action_attrs(dict_action)
    try:
        vnic_str = get_val_from_list_attrs(custom_action_attrs, VNIC_NAME)
    except KeyError:
        yield dict_action  # not a Cloud Provider action
    else:
        for vnic in get_vnic_list(vnic_str):
            new_dict_action = deepcopy(dict_action)
            custom_action_attrs = get_custom_action_attrs(new_dict_action)
            set_val_to_list_attrs(custom_action_attrs, VNIC_NAME, vnic)
            yield new_dict_action


def validate_vnic_for_vm(dict_actions: list[dict]) -> None:
    """Validate that vNIC specified in all actions for VM or none."""
    map_vm_specified_vnic = {}
    for action in dict_actions:
        custom_action_attrs = get_custom_action_attrs(action)
        try:
            vm_uuid = get_val_from_list_attrs(custom_action_attrs, VM_UUID)
        except KeyError:
            continue  # not a Cloud Provider action
        try:
            vnic_name = get_val_from_list_attrs(custom_action_attrs, VNIC_NAME)
        except KeyError:
            specified_vnic = False
        else:
            specified_vnic = bool(vnic_name)

        if (
            vm_uuid in map_vm_specified_vnic
            and map_vm_specified_vnic[vm_uuid] != specified_vnic
        ):
            raise ConnectivityException(
                "You can't specify vNIC for some VM interfaces and not specify for "
                "others"
            )
        map_vm_specified_vnic[vm_uuid] = specified_vnic


def get_vnic_list(vnic_str: str) -> list[str]:
    return re.split(r"[,;]", vnic_str)
