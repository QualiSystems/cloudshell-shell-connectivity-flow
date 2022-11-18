from __future__ import annotations

import re
from copy import deepcopy

from cloudshell.shell.flows.connectivity.helpers.dict_action_helpers import (
    get_val_from_list_attrs,
    set_val_to_list_attrs,
)


def get_custom_action_attrs(dict_action: dict) -> list[dict[str, str]]:
    return dict_action["customActionAttributes"]


def iterate_dict_actions_by_requested_vnic(dict_action: dict):
    """Iterates over dict actions by requested vNIC."""
    custom_action_attrs = get_custom_action_attrs(dict_action)
    try:
        vnic_str = get_val_from_list_attrs(custom_action_attrs, "Vnic Name")
    except KeyError:
        yield dict_action  # not a Cloud Provider action
    else:
        for vnic in get_vnic_list(vnic_str):
            new_dict_action = deepcopy(dict_action)
            custom_action_attrs = get_custom_action_attrs(new_dict_action)
            set_val_to_list_attrs(custom_action_attrs, "Vnic Name", vnic)
            yield new_dict_action


def get_vnic_list(vnic_str: str) -> list[str]:
    return re.split(r"[,;]", vnic_str)
