import pytest

from cloudshell.shell.flows.connectivity.exceptions import VLANHandlerException
from cloudshell.shell.flows.connectivity.helpers.vlan_helper import (
    _sort_vlans,
    _validate_vlan_number,
    get_vlan_list,
    iterate_dict_actions_by_vlan_range,
)


@pytest.mark.parametrize(
    ("vlan_in", "vlan_out"),
    (
        (["5", "33", "11", "2"], ["2", "5", "11", "33"]),
        (["5", "11-30", "33", "7"], ["5", "7", "11-30", "33"]),
        (["1", "101", "2"], ["1", "2", "101"]),
    ),
)
def test_sort_vlan(vlan_in, vlan_out):
    assert vlan_out == _sort_vlans(vlan_in)


@pytest.mark.parametrize(
    ("number", "error", "emsg"),
    (
        ("4095", VLANHandlerException, "Wrong VLAN detected"),
        ("abc", VLANHandlerException, "isn't a integer"),
    ),
)
def test_validate_vlan_number_failed(number, error, emsg):
    with pytest.raises(error, match=emsg):
        _validate_vlan_number(number)


@pytest.mark.parametrize(
    ("vlan_str", "vlan_list", "vlan_range", "multi_vlan"),
    (
        ("10-15,19,21-23", ["10-15", "19", "21-23"], True, False),
        ("12-10", ["10", "11", "12"], False, False),
        ("12-10", ["10,11,12"], False, True),
    ),
)
def test_get_vlan_list(vlan_str, vlan_list, vlan_range, multi_vlan):
    assert vlan_list == get_vlan_list(
        vlan_str, is_vlan_range_supported=vlan_range, is_multi_vlan_supported=multi_vlan
    )


@pytest.mark.parametrize(
    ("vlan_str", "error", "match", "vlan_range", "multi_vlan"),
    (
        ("5000", VLANHandlerException, "Wrong VLAN detected 5000", True, True),
        ("4000-5005", VLANHandlerException, "Wrong VLAN detected 5005", True, True),
    ),
)
def test_get_vlan_list_failed(vlan_str, error, match, vlan_range, multi_vlan):
    with pytest.raises(error, match=match):
        get_vlan_list(
            vlan_str,
            is_vlan_range_supported=vlan_range,
            is_multi_vlan_supported=multi_vlan,
        )


def test_iterate_dict_actions_by_vlan_range():
    dict_action = {
        "connectionParams": {"vlanId": "10,11"},
        "type": "setVlan",
    }

    new_actions = list(
        iterate_dict_actions_by_vlan_range(
            dict_action, is_vlan_range_supported=True, is_multi_vlan_supported=False
        )
    )
    assert [
        {"connectionParams": {"vlanId": "10"}, "type": "setVlan"},
        {"connectionParams": {"vlanId": "11"}, "type": "setVlan"},
    ] == new_actions
