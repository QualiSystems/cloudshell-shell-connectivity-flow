import json
from unittest.mock import Mock

import pytest

from cloudshell.shell.flows.connectivity.basic_flow import AbstractConnectivityFlow
from cloudshell.shell.flows.connectivity.models.connectivity_model import (
    ConnectivityActionModel,
)
from cloudshell.shell.flows.connectivity.models.driver_response import (
    ConnectivityActionResult,
)
from cloudshell.shell.flows.connectivity.parse_request_service import (
    ParseConnectivityRequestService,
)

from tests.cloudshell.shell.flows.connectivity.conftest import create_driver_str_request


@pytest.fixture()
def parse_connectivity_request_service():
    return ParseConnectivityRequestService(
        is_vlan_range_supported=True, is_multi_vlan_supported=True
    )


@pytest.fixture()
def connectivity_flow(parse_connectivity_request_service, logger):
    class ConnectivityFlow(AbstractConnectivityFlow):
        IS_SUCCESS = True

        def _generic_change_vlan_fn(
            self, action: ConnectivityActionModel
        ) -> ConnectivityActionResult:
            if self.IS_SUCCESS:
                return ConnectivityActionResult.success_result_vm(
                    action, "successful", "mac address"
                )
            else:
                return ConnectivityActionResult.fail_result(action, "fail")

        _set_vlan = _generic_change_vlan_fn
        _remove_vlan = _generic_change_vlan_fn

    return ConnectivityFlow(parse_connectivity_request_service, logger)


def test_connectivity_flow(connectivity_flow, driver_request):
    res = connectivity_flow.apply_connectivity(json.dumps(driver_request))
    assert res == (
        '{"driverResponse": {"actionResults": [{'
        '"actionId": "96582265-2728-43aa-bc97-cefb2457ca44_0900c4b5-0f90-42e3-b495", '
        '"type": "removeVlan", '
        '"updatedInterface": "mac address", '
        '"infoMessage": "successful", '
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
                    "updatedInterface": "centos",
                    "infoMessage": "",
                    "errorMessage": "fail",
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
        '"updatedInterface": "mac address", '
        '"infoMessage": "successful", '
        '"errorMessage": "", '
        '"success": true'
        "}]}}"
    )


def test_connectivity_flow_abstract_methods(parse_connectivity_request_service, logger):
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        AbstractConnectivityFlow(parse_connectivity_request_service, logger)


def test_abstract_methods_raises(
    parse_connectivity_request_service, logger, action_model
):
    class TestClass(AbstractConnectivityFlow):
        def _set_vlan(self, action: ConnectivityActionModel) -> str:
            return super()._set_vlan(action_model)

        def _remove_vlan(self, action: ConnectivityActionModel) -> str:
            return super()._remove_vlan(action_model)

    inst = TestClass(parse_connectivity_request_service, logger)
    with pytest.raises(NotImplementedError):
        inst._set_vlan(action_model)

    with pytest.raises(NotImplementedError):
        inst._remove_vlan(action_model)


def test_set_vlan_request_returns_one_response_action(
    create_networking_action_request, connectivity_flow
):
    action = create_networking_action_request(set_vlan=True)
    request = create_driver_str_request(action)

    res = connectivity_flow.apply_connectivity(request)

    assert res
    action_results = json.loads(res)["driverResponse"]["actionResults"]
    assert len(action_results) == 1


def test_do_not_run_set_vlan_if_remove_vlan_failed(
    create_networking_action_request, connectivity_flow
):
    action = create_networking_action_request(set_vlan=True)
    request = create_driver_str_request(action)

    connectivity_flow.IS_SUCCESS = False
    connectivity_flow._set_vlan = Mock()
    res = connectivity_flow.apply_connectivity(request)

    assert res
    action_results = json.loads(res)["driverResponse"]["actionResults"]
    assert len(action_results) == 1
    assert action_results[0]["success"] is False
    connectivity_flow._set_vlan.assert_not_called()


def test_do_run_set_vlan_if_remove_vlan_success(
    create_networking_action_request, parse_connectivity_request_service, logger
):
    def return_success_result(action):
        return ConnectivityActionResult.success_result(action, "successful")

    class TestedConnectivityFlow(AbstractConnectivityFlow):
        _remove_vlan = Mock(side_effect=return_success_result)
        _set_vlan = Mock(side_effect=return_success_result)

    action = create_networking_action_request(set_vlan=True)
    request = create_driver_str_request(action)

    flow = TestedConnectivityFlow(parse_connectivity_request_service, logger)
    res = flow.apply_connectivity(request)

    assert res
    flow._remove_vlan.assert_called_once()
    flow._set_vlan.assert_called_once()


def test_failed_response_if_remove_vlan_failed(
    create_networking_action_request, parse_connectivity_request_service, logger
):
    class TestedConnectivityFlow(AbstractConnectivityFlow):
        def _remove_vlan(self, action: ConnectivityActionModel) -> str:
            1 / 0

        _set_vlan = None

    action = create_networking_action_request(set_vlan=False)
    request = create_driver_str_request(action)

    flow = TestedConnectivityFlow(parse_connectivity_request_service, logger)
    res = flow.apply_connectivity(request)

    assert res
    res = json.loads(res)
    assert len(res["driverResponse"]["actionResults"]) == 1
    action_result = res["driverResponse"]["actionResults"][0]
    assert action_result["success"] is False
    emsg = "division by zero"
    assert emsg in action_result["errorMessage"]
