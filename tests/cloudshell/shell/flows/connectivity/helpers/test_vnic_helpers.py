import pytest

from cloudshell.shell.flows.connectivity.exceptions import ConnectivityException
from cloudshell.shell.flows.connectivity.helpers.dict_action_helpers import (
    get_val_from_list_attrs,
    set_val_to_list_attrs,
)
from cloudshell.shell.flows.connectivity.helpers.vnic_helpers import (
    get_custom_action_attrs,
    get_vnic_list,
    iterate_dict_actions_by_requested_vnic,
    validate_vnic_for_vm,
)


@pytest.mark.parametrize(
    ("vnic_str", "vnic_list"),
    (
        ("Network adapter 1", ["Network adapter 1"]),
        (
            "Network adapter 1,Network adapter 2",
            ["Network adapter 1", "Network adapter 2"],
        ),
        (
            "Network adapter 1;Network adapter 2",
            ["Network adapter 1", "Network adapter 2"],
        ),
        (
            "Network adapter 1,Network adapter 2;Network adapter 3",
            ["Network adapter 1", "Network adapter 2", "Network adapter 3"],
        ),
    ),
)
def test_get_vnic_list(vnic_str, vnic_list):
    assert vnic_list == get_vnic_list(vnic_str)


def test_iterate_dict_actions_by_requested_vnic(action_request):
    custom_action_attrs = get_custom_action_attrs(action_request)
    set_val_to_list_attrs(
        custom_action_attrs, "Vnic Name", "Network adapter 1,Network adapter 2"
    )

    new_actions = list(iterate_dict_actions_by_requested_vnic(action_request))
    assert len(new_actions) == 2
    action1, action2 = new_actions

    custom_action_attrs1 = get_custom_action_attrs(action1)
    getval1 = get_val_from_list_attrs(custom_action_attrs1, "Vnic Name")
    assert getval1 == "Network adapter 1"

    custom_action_attrs2 = get_custom_action_attrs(action2)
    getval2 = get_val_from_list_attrs(custom_action_attrs2, "Vnic Name")
    assert getval2 == "Network adapter 2"


def test_validate_vnic_for_vm(create_networking_action_request):
    action1 = create_networking_action_request(True, vm_uuid="vm1", vnic="vnic1")
    action2 = create_networking_action_request(True, vm_uuid="vm1", vnic="vnic2")
    action3 = create_networking_action_request(True, vm_uuid="vm2", vnic="vnic1")
    actions = [action1, action2, action3]

    # finish without exception
    validate_vnic_for_vm(actions)


def test_validate_not_all_vnic_specified(create_networking_action_request):
    action1 = create_networking_action_request(True, vm_uuid="vm1", vnic="vnic1")
    action2 = create_networking_action_request(True, vm_uuid="vm1")
    action3 = create_networking_action_request(True, vm_uuid="vm2", vnic="vnic1")
    actions = [action1, action2, action3]

    with pytest.raises(ConnectivityException):
        validate_vnic_for_vm(actions)
