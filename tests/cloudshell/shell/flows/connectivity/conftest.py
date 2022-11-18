from __future__ import annotations

import json
from unittest.mock import Mock

import pytest

from cloudshell.shell.flows.connectivity.models.connectivity_model import (
    ConnectionModeEnum,
    ConnectivityActionModel,
)


@pytest.fixture()
def logger():
    return Mock(name="logger")


@pytest.fixture()
def action_request():
    return {
        "connectionId": "96582265-2728-43aa-bc97-cefb2457ca44",
        "connectionParams": {
            "vlanId": "10-11",
            "mode": "Trunk",
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
                {
                    "attributeName": "VLAN ID",
                    "attributeValue": "10-11",
                    "type": "vlanServiceAttribute",
                },
                {
                    "attributeName": "Virtual Network",
                    "attributeValue": "10-11",
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


@pytest.fixture()
def driver_request(action_request):
    return {"driverRequest": {"actions": [action_request]}}


@pytest.fixture()
def action_model(action_request):
    return ConnectivityActionModel.parse_obj(action_request)


@pytest.fixture()
def create_networking_action_request():
    def creator(
        set_vlan: bool,
        vlan_id: str = "10",
        mode: ConnectionModeEnum = ConnectionModeEnum.ACCESS,
        qnq: bool = False,
        port_name: str = "swp2",
        vm_uuid: str | None = None,
        vnic: str | None = None,
    ):
        action = {
            "connectionId": "96582265-2728-43aa-bc97-cefb2457ca44",
            "connectionParams": {
                "vlanId": vlan_id,
                "mode": mode.value,
                "vlanServiceAttributes": [
                    {
                        "attributeName": "QnQ",
                        "attributeValue": str(qnq),
                        "type": "vlanServiceAttribute",
                    },
                    {
                        "attributeName": "CTag",
                        "attributeValue": "",
                        "type": "vlanServiceAttribute",
                    },
                    {
                        "attributeName": "VLAN ID",
                        "attributeValue": vlan_id,
                        "type": "vlanServiceAttribute",
                    },
                    {
                        "attributeName": "Virtual Network",
                        "attributeValue": vlan_id,
                        "type": "vlanServiceAttribute",
                    },
                ],
                "type": "setVlanParameter",
            },
            "connectorAttributes": [],
            "actionTarget": {
                "fullName": f"cumulus/{port_name}",
                "fullAddress": "full address",
                "type": "actionTarget",
            },
            "customActionAttributes": [],
            "actionId": "96582265-2728-43aa-bc97-cefb2457ca44_0900c4b5-0f90-42e3-b495",
            "type": "setVlan" if set_vlan else "removeVlan",
        }
        if vm_uuid:
            action["customActionAttributes"].append(
                {
                    "attributeName": "VM_UUID",
                    "attributeValue": vm_uuid,
                    "type": "customAttribute",
                }
            )
        if vnic:
            action["customActionAttributes"].append(
                {
                    "attributeName": "Vnic Name",
                    "attributeValue": vnic,
                    "type": "customAttribute",
                }
            )
        return action

    return creator


def create_driver_str_request(*action_requests):
    return json.dumps({"driverRequest": {"actions": list(action_requests)}})
