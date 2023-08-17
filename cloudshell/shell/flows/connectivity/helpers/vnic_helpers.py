from __future__ import annotations

import re
from collections.abc import Generator
from copy import deepcopy
from typing import TYPE_CHECKING

from .dict_action_helpers import get_val_from_list_attrs, set_val_to_list_attrs

if TYPE_CHECKING:
    from .types import ActionDict, ActionsAttributeDict

VNIC_NAME = "Vnic Name"
VM_UUID = "VM_UUID"
INTERFACE = "Interface"


def get_custom_action_attrs(dict_action: ActionDict) -> list[ActionsAttributeDict]:
    return dict_action["customActionAttributes"]


def get_connector_attrs(dict_action: ActionDict) -> list[ActionsAttributeDict]:
    return dict_action["connectorAttributes"]


def iterate_dict_actions_by_requested_vnic(
    dict_action: ActionDict,
) -> Generator[ActionDict, None, None]:
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


def iterate_dict_actions_by_interface(
    dict_action: ActionDict,
) -> Generator[ActionDict, None, None]:
    """Iterates over dict actions by requested interface."""
    connector_attrs = get_connector_attrs(dict_action)
    try:
        iface_str = get_val_from_list_attrs(connector_attrs, INTERFACE)
    except KeyError:
        yield dict_action  # not a Cloud Provider action or not a remove action
    else:
        for iface in split_list_str(iface_str):
            new_dict_action = deepcopy(dict_action)
            connector_attrs = get_connector_attrs(new_dict_action)
            set_val_to_list_attrs(connector_attrs, INTERFACE, iface)
            yield new_dict_action


def get_vnic_list(vnic_str: str) -> list[str]:
    return split_list_str(vnic_str)


def split_list_str(string: str) -> list[str]:
    return re.split(r"[,;]", string)
