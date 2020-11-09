from __future__ import annotations

from collections.abc import Iterable

from cloudshell.shell.flows.connectivity.exceptions import VLANHandlerException


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


def _sort_vlans(vlans: Iterable[str]) -> list[str]:
    return sorted(vlans, key=lambda v: tuple(map(int, v.split("-"))))


def get_vlan_list(
    vlan_str: str, is_vlan_range_supported: bool, is_multi_vlan_supported: bool
) -> list[str]:
    result: set[str] = set()
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
    vlan_str = dict_action["connectionParams"]["vlanId"]
    for vlan in get_vlan_list(
        vlan_str, is_vlan_range_supported, is_multi_vlan_supported
    ):
        dict_action["connectionParams"]["vlanId"] = vlan
        yield dict_action
