from copy import deepcopy
from typing import Iterable, List, Set

from cloudshell.shell.flows.connectivity.exceptions import VLANHandlerException
from cloudshell.shell.flows.connectivity.models.connectivity_model import (
    ConnectivityActionModel,
)


def _validate_vlan_number(number: str):
    try:
        number = int(number)
    except ValueError:
        raise VLANHandlerException(f"VLAN {number} isn't a integer")
    if number > 4094 or number < 1:
        raise VLANHandlerException(f"Wrong VLAN detected {number}")


def _validate_vlan_range(vlan_range):
    start, end = vlan_range.split("-")
    for vlan_number in (start, end):
        _validate_vlan_number(vlan_number)


def _sort_vlans(vlans: Iterable[str]) -> List[str]:
    return sorted(vlans, key=lambda v: tuple(map(int, v.split("-"))))


def get_vlan_list(
    vlan_str: str, is_vlan_range_supported: bool, is_multi_vlan_supported: bool
) -> List[str]:
    result: Set[str] = set()
    for vlan_range in map(str.strip, vlan_str.split(",")):
        if "-" not in vlan_range:
            _validate_vlan_number(vlan_range)
            result.add(vlan_range)
        else:
            _validate_vlan_range(vlan_range)
            if is_vlan_range_supported:
                result.add(vlan_range)
            else:
                start, end = sorted(map(int, vlan_range.split("-")))
                result.update(map(str, range(start, end + 1)))
    if is_multi_vlan_supported:
        return [",".join(_sort_vlans(result))]
    else:
        return _sort_vlans(result)


def iterate_dict_actions_by_vlan_range(
    dict_action: dict, is_vlan_range_supported: bool, is_multi_vlan_supported: bool
):
    action = ConnectivityActionModel(**dict_action)
    vlan_str = action.connection_params.vlan_service_attrs.vlan_id
    if (
        action.connection_params.mode is action.connection_params.mode.ACCESS
        or action.connection_params.vlan_service_attrs.qnq
    ):
        try:
            int(vlan_str)
        except ValueError:
            emsg = f"Access mode and QnQ can be only with int VLAN, not '{vlan_str}'"
            raise ValueError(emsg)
    for vlan in get_vlan_list(
        vlan_str, is_vlan_range_supported, is_multi_vlan_supported
    ):
        new_dict_action = deepcopy(dict_action)
        for attr_dict in new_dict_action["connectionParams"]["vlanServiceAttributes"]:
            if attr_dict["attributeName"] == "VLAN ID":
                attr_dict["attributeValue"] = vlan
        yield new_dict_action


def patch_virtual_network(dict_action: dict) -> None:
    """Removes Virtual Network if it's equal to VLAN ID.

    Virtual Network can contain name or ID of the existed network for this user should
    edit the attribute in Resource Manager.
    By default, Virtual Network contains VLAN ID.
    """
    vlan_id = None
    for attr_dict in dict_action["connectionParams"]["vlanServiceAttributes"]:
        if attr_dict["attributeName"] == "VLAN ID":
            vlan_id = attr_dict["attributeValue"]
            break

    for attr_dict in dict_action["connectionParams"]["vlanServiceAttributes"]:
        if attr_dict["attributeName"] == "Virtual Network":
            if attr_dict["attributeValue"] == str(vlan_id):
                attr_dict["attributeValue"] = None
            break
