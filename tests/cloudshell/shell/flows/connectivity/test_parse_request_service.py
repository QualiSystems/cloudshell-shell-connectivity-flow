from __future__ import annotations

import json

import pytest

from cloudshell.shell.flows.connectivity.helpers.dict_action_helpers import (
    set_val_to_list_attrs,
)
from cloudshell.shell.flows.connectivity.models.connectivity_model import (
    ConnectivityActionModel,
)
from cloudshell.shell.flows.connectivity.parse_request_service import (
    AbstractParseConnectivityService,
    ParseConnectivityRequestService,
)


def test_abstract_parse_connectivity_request_service_initialize():
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        AbstractParseConnectivityService()


def test_abstract_parse_connectivity_request_service_get_actions_raises(driver_request):
    class TestClass(AbstractParseConnectivityService):
        def get_actions(self, request: str) -> list[ConnectivityActionModel]:
            return super().get_actions(request)

    service = TestClass()
    with pytest.raises(NotImplementedError):
        service.get_actions(driver_request)


def test_parse_connectivity_request_service(driver_request):
    service = ParseConnectivityRequestService(
        is_vlan_range_supported=False, is_multi_vlan_supported=False
    )
    actions = service.get_actions(json.dumps(driver_request))
    assert len(actions) == 2
    first, second = actions
    assert first.connection_params.vlan_id == "10"
    assert second.connection_params.vlan_id == "11"
    assert first.action_id == second.action_id
    assert not first.connection_params.vlan_service_attrs.virtual_network


def test_parse_connectivity_without_vlan_id_in_vlan_service(driver_request):
    # in VLAN Auto mode, the VLAN ID is not provided in the VLAN Service
    action_request = driver_request["driverRequest"]["actions"][0]
    service_attrs = action_request["connectionParams"]["vlanServiceAttributes"]
    set_val_to_list_attrs(service_attrs, "VLAN ID", "")
    assert action_request["connectionParams"]["vlanId"] == "10-11"

    service = ParseConnectivityRequestService(
        is_vlan_range_supported=True, is_multi_vlan_supported=True
    )
    actions = service.get_actions(json.dumps(driver_request))

    assert len(actions) == 1
    action = actions[0]
    assert action.connection_params.vlan_id == "10-11"
    assert not action.connection_params.vlan_service_attrs.virtual_network
    assert action.connection_params.vlan_service_attrs.vlan_id == "10-11"
