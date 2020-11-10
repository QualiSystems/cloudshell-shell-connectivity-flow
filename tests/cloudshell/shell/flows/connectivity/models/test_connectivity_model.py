import json

from cloudshell.shell.flows.connectivity.models.connectivity_model import (
    ConnectivityActionModel,
    get_actions_from_request,
)


def test_connectivity_action_model(action_request):
    action = ConnectivityActionModel.parse_obj(action_request)
    assert action.action_id == action_request["actionId"]
    assert action.type is action.type.REMOVE_VLAN
    assert action.type.value == "removeVlan"
    assert action.connection_id == action_request["connectionId"]
    assert action.connection_params.vlan_id == "10-11"
    assert action.connection_params.mode is action.connection_params.mode.ACCESS
    assert action.connection_params.mode.value == "Access"
    assert action.connection_params.vlan_service_attrs.qnq is False
    assert action.connection_params.vlan_service_attrs.ctag == ""
    assert action.connector_attrs.interface == "mac address"
    assert action.action_target.name == "centos"
    assert action.action_target.address == "full address"
    assert action.custom_action_attrs.vm_uuid == "vm_uid"
    assert action.custom_action_attrs.vnic == "vnic"


def test_get_actions_from_request(driver_request):
    actions = get_actions_from_request(
        json.dumps(driver_request),
        ConnectivityActionModel,
        is_vlan_range_supported=False,
        is_multi_vlan_supported=False,
    )
    assert len(actions) == 2
    first, second = actions
    assert first.connection_params.vlan_id == "10"
    assert second.connection_params.vlan_id == "11"
    assert first.action_id == second.action_id
