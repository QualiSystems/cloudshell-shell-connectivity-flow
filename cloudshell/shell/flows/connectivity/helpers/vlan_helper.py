from __future__ import annotations

from collections.abc import Generator, Iterable
from copy import deepcopy
from typing import TYPE_CHECKING, Any

from attrs import define

from .dict_action_helpers import get_val_from_list_attrs, set_val_to_list_attrs
from cloudshell.shell.flows.connectivity.exceptions import VLANHandlerException
from cloudshell.shell.flows.connectivity.models.connectivity_model import (
    ConnectionModeEnum,
    ConnectivityActionModel,
)

if TYPE_CHECKING:
    from .types import ActionDict, ActionsAttributeDict

VLAN_ID = "VLAN ID"
VIRTUAL_NETWORK = "Virtual Network"


@define
class VlanContainNotInt(VLANHandlerException):
    value: Any

    def __str__(self) -> str:
        return f"VLAN {self.value} isn't a integer"


@define
class VirtualNetworkDeprecated(VLANHandlerException):
    def __str__(self) -> str:
        return (
            "'Virtual Network' attribute is deprecated, use 'Existing Network' instead"
        )


def _validate_vlan_number(str_number: str) -> None:
    try:
        number = int(str_number)
    except ValueError:
        raise VlanContainNotInt(str_number)
    if not 1 <= number <= 4094:
        raise VLANHandlerException(f"Wrong VLAN detected {number}")


def _validate_vlan_range(vlan_range: str) -> None:
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
    dict_action: ActionDict,
    is_vlan_range_supported: bool,
    is_multi_vlan_supported: bool,
) -> Generator[ActionDict, None, None]:
    action = ConnectivityActionModel.parse_obj(dict_action)
    vlan_str = action.connection_params.vlan_service_attrs.vlan_id
    if (
        action.connection_params.mode is ConnectionModeEnum.ACCESS
        or action.connection_params.vlan_service_attrs.qnq
    ):
        try:
            int(vlan_str)
        except ValueError:
            emsg = f"Access mode and QnQ can be only with int VLAN, not '{vlan_str}'"
            try:
                get_vlan_list(vlan_str, False, False)
            except VlanContainNotInt:
                raise VirtualNetworkDeprecated
            except Exception:
                raise ValueError(emsg)
            else:
                raise ValueError(emsg)
    for vlan in get_vlan_list(
        vlan_str, is_vlan_range_supported, is_multi_vlan_supported
    ):
        new_dict_action = deepcopy(dict_action)
        new_dict_action["connectionParams"]["vlanId"] = vlan
        vlan_service_attrs = get_vlan_service_attrs(new_dict_action)
        set_val_to_list_attrs(vlan_service_attrs, VLAN_ID, vlan)
        yield new_dict_action


def patch_vlan_service_vlan_id(dict_action: ActionDict) -> None:
    """VLAN ID in VLAN service attributes can be empty."""
    vlan_id = dict_action["connectionParams"]["vlanId"]
    vlan_service_attrs = get_vlan_service_attrs(dict_action)
    set_val_to_list_attrs(vlan_service_attrs, VLAN_ID, vlan_id)


def patch_virtual_network(dict_action: ActionDict) -> None:
    """Removes Virtual Network if it's equal to VLAN ID.

    Virtual Network can contain name or ID of the existed network for this user should
    edit the attribute in Resource Manager.
    By default, Virtual Network contains VLAN ID.
    """
    vlan_service_attrs = get_vlan_service_attrs(dict_action)
    vlan_id = get_val_from_list_attrs(vlan_service_attrs, VLAN_ID)
    set_val_to_list_attrs(
        vlan_service_attrs, VIRTUAL_NETWORK, "", set_if_eq=str(vlan_id)
    )


def get_vlan_service_attrs(dict_action: ActionDict) -> list[ActionsAttributeDict]:
    return dict_action["connectionParams"]["vlanServiceAttributes"]
