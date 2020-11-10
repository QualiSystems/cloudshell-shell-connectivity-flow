import json

from cloudshell.shell.flows.connectivity.models.connectivity_model import (
    ConnectivityActionModel,
    get_actions_from_request,
)

ACTION_REQUEST = {
    "connectionId": "96582265-2728-43aa-bc97-cefb2457ca44",
    "connectionParams": {
        "vlanId": "10-11",
        "mode": "Access",
        "vlanServiceAttributes": [
            {
                "attributeName": "QnQ",
                "attributeValue": "False",
                "type": "vlanServiceAttribute",
            },
            {
                "attributeName": "CTag",
                "attributeValue": "",
                "type": "vlanServiceAttribute",
            },
        ],
        "type": "setVlanParameter",
    },
    "connectorAttributes": [
        {
            "attributeName": "Selected Network",
            "attributeValue": "2",
            "type": "connectorAttribute",
        },
        {
            "attributeName": "Interface",
            "attributeValue": "mac address",
            "type": "connectorAttribute",
        },
    ],
    "actionTarget": {
        "fullName": "centos",
        "fullAddress": "full address",
        "type": "actionTarget",
    },
    "customActionAttributes": [
        {
            "attributeName": "VM_UUID",
            "attributeValue": "vm_uid",
            "type": "customAttribute",
        },
        {
            "attributeName": "Vnic Name",
            "attributeValue": "vnic",
            "type": "customAttribute",
        },
    ],
    "actionId": "96582265-2728-43aa-bc97-cefb2457ca44_0900c4b5-0f90-42e3-b495",
    "type": "removeVlan",
}


def test_connectivity_action_model():
    action = ConnectivityActionModel.parse_obj(ACTION_REQUEST)
    assert action.action_id == ACTION_REQUEST["actionId"]
    assert action.type is action.type.REMOVE_VLAN
    assert action.type.value == "removeVlan"
    assert action.connection_id == ACTION_REQUEST["connectionId"]
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


def test_get_actions_from_request():
    request = {"driverRequest": {"actions": [ACTION_REQUEST]}}
    actions = get_actions_from_request(
        json.dumps(request),
        ConnectivityActionModel,
        is_vlan_range_supported=False,
        is_multi_vlan_supported=False,
    )
    assert len(actions) == 2
    first, second = actions
    assert first.connection_params.vlan_id == "10"
    assert second.connection_params.vlan_id == "11"
    assert first.action_id == second.action_id
