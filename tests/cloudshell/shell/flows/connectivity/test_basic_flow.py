import json

import pytest

from cloudshell.shell.flows.connectivity.basic_flow import AbstractConnectivityFlow
from cloudshell.shell.flows.connectivity.models.connectivity_model import (
    ConnectivityActionModel,
)


@pytest.fixture()
def connectivity_flow(logger):
    class ConnectivityFlow(AbstractConnectivityFlow):
        IS_SUCCESS = True

        def _generic_change_vlan_fn(self, action: ConnectivityActionModel) -> str:
            if self.IS_SUCCESS:
                return "success msg"
            else:
                raise Exception("error msg")

        _set_vlan = _generic_change_vlan_fn
        _remove_vlan = _generic_change_vlan_fn
        _remove_all_vlans = _generic_change_vlan_fn

    return ConnectivityFlow(logger)


def test_connectivity_flow(connectivity_flow, driver_request):
    res = connectivity_flow.apply_connectivity(json.dumps(driver_request))
    assert res == (
        '{"driverResponse": {"actionResults": [{'
        '"actionId": "96582265-2728-43aa-bc97-cefb2457ca44_0900c4b5-0f90-42e3-b495", '
        '"type": "removeVlan", '
        '"updateInterface": "centos", '
        '"infoMessage": "Vlan 10-11 configuration successfully completed", '
        '"errorMessage": "", '
        '"success": true'
        "}]}}"
    )


def test_connectivity_flow_failed(connectivity_flow, driver_request):
    connectivity_flow.IS_SUCCESS = False
    res = connectivity_flow.apply_connectivity(json.dumps(driver_request))
    assert json.loads(res) == {
        "driverResponse": {
            "actionResults": [
                {
                    "actionId": (
                        "96582265-2728-43aa-bc97-cefb2457ca44_0900c4b5-0f90-42e3-b495"
                    ),
                    "type": "removeVlan",
                    "updateInterface": "centos",
                    "infoMessage": "",
                    "errorMessage": (
                        "Vlan 10-11 configuration failed.\n"
                        "Vlan configuration details:\n"
                        "error msg"
                    ),
                    "success": False,
                }
            ]
        }
    }


def test_connectivity_flow_set_vlan(connectivity_flow, driver_request):
    driver_request["driverRequest"]["actions"][0]["type"] = "setVlan"
    res = connectivity_flow.apply_connectivity(json.dumps(driver_request))
    assert res == (
        '{"driverResponse": {"actionResults": [{'
        '"actionId": "96582265-2728-43aa-bc97-cefb2457ca44_0900c4b5-0f90-42e3-b495", '
        '"type": "setVlan", '
        '"updateInterface": "centos", '
        '"infoMessage": "Vlan 10-11 configuration successfully completed", '
        '"errorMessage": "", '
        '"success": true'
        "}]}}"
    )


def test_abstract_methods_do_nothing(logger, action_model):
    class TestClass(AbstractConnectivityFlow):
        pass

    inst = TestClass(logger)
    assert inst._set_vlan(action_model) is None
    assert inst._remove_all_vlans(action_model) is None
    assert inst._remove_vlan(action_model) is None
