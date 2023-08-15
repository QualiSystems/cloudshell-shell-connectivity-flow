from __future__ import annotations

import pytest

from cloudshell.shell.flows.connectivity.models.connectivity_model import (
    ConnectivityActionModel,
)
from cloudshell.shell.flows.connectivity.parse_request_service import (
    ParseConnectivityRequestService,
)


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
def parse_connectivity_request_service():
    return ParseConnectivityRequestService(
        is_vlan_range_supported=True, is_multi_vlan_supported=True
    )
