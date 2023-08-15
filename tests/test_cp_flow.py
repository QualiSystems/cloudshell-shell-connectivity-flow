from __future__ import annotations

from typing import Any
from unittest.mock import Mock, call
from uuid import uuid4

import pytest
from attrs import define, field

from cloudshell.shell.flows.connectivity.cloud_providers_flow import (
    AbcCloudProviderConnectivityFlow,
    VnicInfo,
)
from cloudshell.shell.flows.connectivity.models.connectivity_model import (
    ConnectivityActionModel,
    get_vnic,
)
from tests.base import (
    DEFAULT_VM_UUID,
    TestConnectivityFlowHelper,
    check_successful_result,
    create_cp_ad,
    create_request,
    get_actions,
    get_one_action,
    get_one_result,
    get_results,
)


@define
class ConnectivityFlow(TestConnectivityFlowHelper, AbcCloudProviderConnectivityFlow):
    is_clear_success: bool | list[bool] = True
    is_set_success: bool | list[bool] = True
    is_remove_success: bool | list[bool] = True
    manager = field(factory=Mock)
    vnics = field(factory=list)
    def_vm = field(init=False)
    vms = field(factory=dict)

    def __attrs_post_init__(self):
        self.def_vm = Mock(macs={i: str(uuid4()) for i in range(1, 11)})
        self.vnics = [VnicInfo("Network adapter 1", 1, True)]
        self.vms = {DEFAULT_VM_UUID: self.def_vm}

    def get_vnics(self, vm: Any) -> list[VnicInfo]:
        return self.vnics

    def load_target(self, target_name: str) -> Any:
        return self.vms[target_name]

    def set_vlan(self, action: ConnectivityActionModel, target: Any) -> str:
        super().set_vlan(action, target)
        return target.macs[int(get_vnic(action))]


@pytest.fixture()
def cf(parse_connectivity_request_service):
    return ConnectivityFlow(
        parse_connectivity_request_service=parse_connectivity_request_service
    )


def test_one_set_vlan(cf):
    """Request contains one set VLAN action without vnic specified.

    - execute set VLAN action
    - return success response
    """
    request = create_request(create_cp_ad(set_vlan=True, vnic=None))

    resp_str = cf.apply_connectivity(request)

    action = get_one_action(cf)
    expected_calls = [
        call.set_vlan(action, cf.def_vm),
    ]
    assert cf.manager.mock_calls == expected_calls
    assert get_vnic(action) == "1"

    result = get_one_result(resp_str)
    check_successful_result(result, action, targets=[cf.def_vm.macs[1]])


def test_set_vlan_first_vnic_cannot_be_used(cf):
    """Request contains one set VLAN action without vnic specified.

    - VM has 2 vNICs - 1st vNIC cannot be used, 2nd vNIC can be used
    - execute set VLAN action on 2nd vNIC
    - return success response
    """
    request = create_request(create_cp_ad(set_vlan=True, vnic=None))
    cf.vnics = [
        VnicInfo("Network adapter 1", 1, False),
        VnicInfo("Network adapter 2", 2, True),
    ]

    resp_str = cf.apply_connectivity(request)

    action = get_one_action(cf)
    expected_calls = [
        call.set_vlan(action, cf.def_vm),
    ]
    assert cf.manager.mock_calls == expected_calls
    assert get_vnic(action) == "2"

    result = get_one_result(resp_str)
    check_successful_result(result, action, targets=[cf.def_vm.macs[2]])


def test_set_vlan_vnic_specified(cf):
    """Request contains one set VLAN action with vnic specified.

    - VM has 1 vnic that can be used
    - execute set VLAN action
    - return success response
    """
    request = create_request(create_cp_ad(set_vlan=True, vnic="Network adapter 1"))

    resp_str = cf.apply_connectivity(request)

    action = get_one_action(cf)
    expected_calls = [
        call.set_vlan(action, cf.def_vm),
    ]
    assert cf.manager.mock_calls == expected_calls
    assert get_vnic(action) == "1"

    result = get_one_result(resp_str)
    check_successful_result(result, action, targets=[cf.def_vm.macs[1]])


def test_set_vlan_vnic_specified_exists_but_cannot_be_used(cf):
    """Request contains one set VLAN action with vnic specified.

    - VM has 1 vnic that cannot be used
    - return error response
    """
    request = create_request(create_cp_ad(set_vlan=True, vnic="Network adapter 1"))
    cf.vnics = [VnicInfo("Network adapter 1", 1, False)]

    with pytest.raises(ValueError, match="Cannot connect to vNIC 1"):
        cf.apply_connectivity(request)

    action = get_one_action(cf)
    assert cf.manager.mock_calls == []
    assert get_vnic(action) == "1"


def test_set_vlan_specified_doesnt_exists(cf):
    """Request contains one set VLAN action with vnic specified.

    - VM has one vnic but in request another vnic is specified
    - execute set VLAN action
    - return success response
    """
    request = create_request(create_cp_ad(set_vlan=True, vnic="Network adapter 2"))
    cf.vnics = [VnicInfo("Network adapter 1", 1, True)]

    resp_str = cf.apply_connectivity(request)

    action = get_one_action(cf)
    expected_calls = [
        call.set_vlan(action, cf.def_vm),
    ]
    assert cf.manager.mock_calls == expected_calls
    assert get_vnic(action) == "2"

    result = get_one_result(resp_str)
    check_successful_result(result, action, targets=[cf.def_vm.macs[2]])


def test_set_vlan_specified_doesnt_exists_and_cannot_be_used(cf):
    """Request contains one set VLAN action with vnic specified.

    - VM has one vnic but in request another vnic is specified
    - vnic cannot be created cause gap of vnic indexes
    """
    request = create_request(create_cp_ad(set_vlan=True, vnic="3"))
    cf.vnics = [VnicInfo("Network adapter 1", 1, True)]

    with pytest.raises(ValueError, match="There are gaps between vNIC indexes"):
        cf.apply_connectivity(request)

    action = get_one_action(cf)
    assert cf.manager.mock_calls == []
    assert get_vnic(action) == "3"


def test_set_vlan_with_several_vnics(cf):
    """Request contains 2 set VLAN actions, both with 2 vnic specified.

    - VM has 2 vnics that can be used
    - execute set VLAN actions
    - return success response
    """
    set_ad1 = create_cp_ad(set_vlan=True, vnic="1,3", vlan_id="11")
    set_ad2 = create_cp_ad(set_vlan=True, vnic="2;4", vlan_id="12")
    request = create_request(set_ad1, set_ad2)
    cf.vnics = [
        VnicInfo("Network adapter 1", 1, True),
        VnicInfo("Network adapter 2", 2, True),
    ]
    set_ad1_1 = create_cp_ad(
        set_vlan=True, vnic="1", vlan_id="11", action_id=set_ad1["actionId"]
    )
    set_ad1_3 = create_cp_ad(
        set_vlan=True, vnic="3", vlan_id="11", action_id=set_ad1["actionId"]
    )
    set_ad2_2 = create_cp_ad(
        set_vlan=True, vnic="2", vlan_id="12", action_id=set_ad2["actionId"]
    )
    set_ad2_4 = create_cp_ad(
        set_vlan=True, vnic="4", vlan_id="12", action_id=set_ad2["actionId"]
    )

    resp_str = cf.apply_connectivity(request)

    set_action1_1, set_action1_3, set_action2_2, set_action2_4 = get_actions(
        cf, set_ad1_1, set_ad1_3, set_ad2_2, set_ad2_4
    )
    expected_calls = [
        call.set_vlan(set_action1_1, cf.def_vm),
        call.set_vlan(set_action2_2, cf.def_vm),
        call.set_vlan(set_action1_3, cf.def_vm),
        call.set_vlan(set_action2_4, cf.def_vm),
    ]
    assert cf.manager.mock_calls == expected_calls
    assert get_vnic(set_action1_1) == "1"
    assert get_vnic(set_action1_3) == "3"
    assert get_vnic(set_action2_2) == "2"
    assert get_vnic(set_action2_4) == "4"

    set_res1, set_res2 = get_results(resp_str, set_ad1, set_ad2)
    check_successful_result(
        set_res1, set_action1_1, targets=[cf.def_vm.macs[1], cf.def_vm.macs[3]]
    )
    check_successful_result(
        set_res2, set_action2_2, targets=[cf.def_vm.macs[2], cf.def_vm.macs[4]]
    )
