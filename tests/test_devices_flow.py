from __future__ import annotations

from unittest.mock import Mock, call

import pytest
from attrs import define, field

from cloudshell.shell.flows.connectivity.devices_flow import AbcDeviceConnectivityFlow
from cloudshell.shell.flows.connectivity.models.connectivity_model import (
    ConnectionModeEnum,
)
from cloudshell.shell.flows.connectivity.parse_request_service import (
    ParseConnectivityRequestService,
)
from tests.base import (
    TestConnectivityFlowHelper,
    check_failed_result,
    check_successful_result,
    create_net_ad,
    create_request,
    get_actions,
    get_one_action,
    get_one_result,
    get_results,
)


@define
class ConnectivityFlow(TestConnectivityFlowHelper, AbcDeviceConnectivityFlow):
    is_clear_success: bool | list[bool] = True
    is_set_success: bool | list[bool] = True
    is_remove_success: bool | list[bool] = True
    manager = field(factory=Mock)


@pytest.fixture()
def connectivity_flow(parse_connectivity_request_service):
    return ConnectivityFlow(
        parse_connectivity_request_service=parse_connectivity_request_service
    )


@pytest.fixture()
def parse_connectivity_request_service():
    return ParseConnectivityRequestService(
        is_vlan_range_supported=False, is_multi_vlan_supported=False
    )


def test_one_set_vlan(connectivity_flow):
    """Request contains one set VLAN action.

    - execute clear for the target
    - execute set VLAN for the target
    - return success response
    """
    request = create_request(create_net_ad(set_vlan=True))

    resp_str = connectivity_flow.apply_connectivity(request)

    action = get_one_action(connectivity_flow)
    expected_calls = [call.clear(action, None), call.set_vlan(action, None)]
    assert connectivity_flow.manager.mock_calls == expected_calls

    result = get_one_result(resp_str)
    check_successful_result(result, action)


def test_one_set_vlan_failed_to_clear(connectivity_flow):
    """Request contains one set VLAN action.

    - execute clear for the target that fails
    - do not execute set VLAN
    - return failed response
    """
    connectivity_flow.is_clear_success = False
    request = create_request(create_net_ad(set_vlan=True))

    resp_str = connectivity_flow.apply_connectivity(request)

    action = get_one_action(connectivity_flow)
    expected_calls = [call.clear(action, None)]
    assert connectivity_flow.manager.mock_calls == expected_calls

    result = get_one_result(resp_str)
    check_failed_result(result, action)


def test_one_set_vlan_failed_to_set(connectivity_flow):
    """Request contains one set VLAN action.

    - execute clear for the target
    - execute set VLAN for the target that fails
    - execute rollback - clear the target
    - return failed response
    """
    connectivity_flow.is_set_success = False
    request = create_request(create_net_ad(set_vlan=True))

    resp_str = connectivity_flow.apply_connectivity(request)

    action = get_one_action(connectivity_flow)
    expected_calls = [
        call.clear(action, None),
        call.set_vlan(action, None),
        call.clear(action, None),
    ]
    assert connectivity_flow.manager.mock_calls == expected_calls

    result = get_one_result(resp_str)
    check_failed_result(result, action)


def test_one_set_vlan_failed_to_set_and_rollback(connectivity_flow):
    """Request contains one set VLAN action.

    - execute clear for the target
    - execute set VLAN for the target that fails
    - execute rollback - clear the target that fails
    - return failed response
    """
    connectivity_flow.is_set_success = False
    connectivity_flow.is_clear_success = [True, False]  # second for rollback
    request = create_request(create_net_ad(set_vlan=True))

    resp_str = connectivity_flow.apply_connectivity(request)

    action = get_one_action(connectivity_flow)
    expected_calls = [
        call.clear(action, None),
        call.set_vlan(action, None),
        call.clear(action, None),
    ]
    assert connectivity_flow.manager.mock_calls == expected_calls

    result = get_one_result(resp_str)
    check_failed_result(result, action)


def test_one_set_and_one_remove_vlan(connectivity_flow):
    """Request contains one set VLAN action and one remove VLAN action.

    - execute clear with set VLAN action
    - execute remove VLAN with remove VLAN action
    - execute set VLAN with set VLAN action
    - return success response with two results
    """
    set_ad = create_net_ad(set_vlan=True)
    remove_ad = create_net_ad(set_vlan=False)
    request = create_request(set_ad, remove_ad)

    resp_str = connectivity_flow.apply_connectivity(request)

    set_action, remove_action = get_actions(connectivity_flow, set_ad, remove_ad)
    expected_calls = [
        call.clear(set_action, None),
        call.remove_vlan(remove_action, None),
        call.set_vlan(set_action, None),
    ]
    assert connectivity_flow.manager.mock_calls == expected_calls

    set_resp, remove_resp = get_results(resp_str, set_ad, remove_ad)
    check_successful_result(set_resp, set_action)
    check_successful_result(remove_resp, remove_action)


def test_one_set_and_one_remove_vlan_failed_to_clear(connectivity_flow):
    """Request contains one set VLAN action and one remove VLAN action.

    - execute clear with set VLAN action that fails
    - execute remove VLAN with remove VLAN action
    - do not execute set VLAN
    - return two results - set VLAN failed, remove VLAN success
    """
    connectivity_flow.is_clear_success = False
    set_ad = create_net_ad(set_vlan=True)
    remove_ad = create_net_ad(set_vlan=False)
    request = create_request(set_ad, remove_ad)

    resp_str = connectivity_flow.apply_connectivity(request)

    set_action, remove_action = get_actions(connectivity_flow, set_ad, remove_ad)
    expected_calls = [
        call.clear(set_action, None),
        call.remove_vlan(remove_action, None),
    ]
    assert connectivity_flow.manager.mock_calls == expected_calls

    set_resp, remove_resp = get_results(resp_str, set_ad, remove_ad)
    check_failed_result(set_resp, set_action)
    check_successful_result(remove_resp, remove_action)


def test_one_set_and_one_remove_vlan_failed_to_remove(connectivity_flow):
    """Request contains one set VLAN action and one remove VLAN action.

    - execute clear with set VLAN action
    - execute remove VLAN with remove VLAN action that fails
    - execute set VLAN with set VLAN action
    - return two results - set VLAN success, remove VLAN failed
    """
    connectivity_flow.is_remove_success = False
    set_ad = create_net_ad(set_vlan=True)
    remove_ad = create_net_ad(set_vlan=False)
    request = create_request(set_ad, remove_ad)

    resp_str = connectivity_flow.apply_connectivity(request)

    set_action, remove_action = get_actions(connectivity_flow, set_ad, remove_ad)
    expected_calls = [
        call.clear(set_action, None),
        call.remove_vlan(remove_action, None),
        call.set_vlan(set_action, None),
    ]
    assert connectivity_flow.manager.mock_calls == expected_calls

    set_resp, remove_resp = get_results(resp_str, set_ad, remove_ad)
    check_successful_result(set_resp, set_action)
    check_failed_result(remove_resp, remove_action)


def test_one_set_and_one_remove_vlan_failed_to_set(connectivity_flow):
    """Request contains one set VLAN action and one remove VLAN action.

    - execute clear with set VLAN action
    - execute remove VLAN with remove VLAN action
    - execute set VLAN with set VLAN action that fails
    - execute rollback - with set VLAN action
    - return two results - set VLAN failed, remove VLAN success
    """
    connectivity_flow.is_set_success = False
    set_ad = create_net_ad(set_vlan=True)
    remove_ad = create_net_ad(set_vlan=False)
    request = create_request(set_ad, remove_ad)

    resp_str = connectivity_flow.apply_connectivity(request)

    set_action, remove_action = get_actions(connectivity_flow, set_ad, remove_ad)
    expected_calls = [
        call.clear(set_action, None),
        call.remove_vlan(remove_action, None),
        call.set_vlan(set_action, None),
        call.clear(set_action, None),
    ]
    assert connectivity_flow.manager.mock_calls == expected_calls

    set_resp, remove_resp = get_results(resp_str, set_ad, remove_ad)
    check_failed_result(set_resp, set_action)
    check_successful_result(remove_resp, remove_action)


def test_several_set_and_remove_actions_some_fails(connectivity_flow):
    """Request contains 4 set VLAN actions and 3 remove VLAN actions.

    - execute clear for all set VLAN actions, 2nd fails, the rest succeeds
    - execute remove VLAN with all VLAN actions, 3rd fails, the rest succeeds
    - execute set VLAN with 1,3,4 set VLAN actions, 3rd and 4th fails, 1st succeeds
    - execute rollback - with 3rd set VLAN action
    - return 7 results - 2nd and 3rd set VLAN failed, 3rd remove VLAN failed
        the rest succeeded
    """
    connectivity_flow.is_clear_success = [True, False, True, True] + [
        True,
        False,  # for rollback failed set VLAN
    ]
    connectivity_flow.is_remove_success = [True, True, False]
    connectivity_flow.is_set_success = [True, False, False]

    set_ad1 = create_net_ad(set_vlan=True, vlan_id="11")
    set_ad2 = create_net_ad(set_vlan=True, vlan_id="12")
    set_ad3 = create_net_ad(set_vlan=True, vlan_id="13")
    set_ad4 = create_net_ad(set_vlan=True, vlan_id="14")
    remove_ad1 = create_net_ad(set_vlan=False, vlan_id="21")
    remove_ad2 = create_net_ad(set_vlan=False, vlan_id="22")
    remove_ad3 = create_net_ad(set_vlan=False, vlan_id="23")
    ads = (set_ad1, set_ad2, set_ad3, set_ad4, remove_ad1, remove_ad2, remove_ad3)
    request = create_request(*ads)

    resp_str = connectivity_flow.apply_connectivity(request)

    (
        set_action1,
        set_action2,
        set_action3,
        set_action4,
        remove_action1,
        remove_action2,
        remove_action3,
    ) = get_actions(connectivity_flow, *ads)
    expected_calls = [
        call.clear(set_action1, None),
        call.clear(set_action2, None),
        call.clear(set_action3, None),
        call.clear(set_action4, None),
        call.remove_vlan(remove_action1, None),
        call.remove_vlan(remove_action2, None),
        call.remove_vlan(remove_action3, None),
        call.set_vlan(set_action1, None),
        call.set_vlan(set_action3, None),
        call.set_vlan(set_action4, None),
        call.clear(set_action3, None),
        call.clear(set_action4, None),
    ]
    assert connectivity_flow.manager.mock_calls == expected_calls

    (
        set_resp1,
        set_resp2,
        set_resp3,
        set_resp4,
        remove_resp1,
        remove_resp2,
        remove_resp3,
    ) = get_results(resp_str, *ads)
    check_successful_result(set_resp1, set_action1)
    check_failed_result(set_resp2, set_action2)
    check_failed_result(set_resp3, set_action3)
    check_failed_result(set_resp4, set_action4)
    check_successful_result(remove_resp1, remove_action1)
    check_successful_result(remove_resp2, remove_action2)
    check_failed_result(remove_resp3, remove_action3)


def test_set_vlan_range(connectivity_flow):
    """Request contains one set VLAN range action that splits to sub actions.

    - execute clear with the last of the set VLAN sub actions
    - execute set VLAN for each VLAN in range
    - return success result - all sub actions success
    """
    set_ad1 = create_net_ad(
        set_vlan=True, vlan_id="11-13", mode=ConnectionModeEnum.TRUNK, uniq_id=False
    )
    request = create_request(set_ad1)
    set_ad1_1 = create_net_ad(set_vlan=True, vlan_id="11", uniq_id=False)
    set_ad1_2 = create_net_ad(set_vlan=True, vlan_id="12", uniq_id=False)
    set_ad1_3 = create_net_ad(set_vlan=True, vlan_id="13", uniq_id=False)

    resp_str = connectivity_flow.apply_connectivity(request)

    set_action1_1, set_action1_2, set_action1_3 = get_actions(
        connectivity_flow, set_ad1_1, set_ad1_2, set_ad1_3
    )
    expected_calls = [
        call.clear(set_action1_3, None),
        call.set_vlan(set_action1_1, None),
        call.set_vlan(set_action1_2, None),
        call.set_vlan(set_action1_3, None),
    ]
    assert connectivity_flow.manager.mock_calls == expected_calls

    set_resp = get_one_result(resp_str)
    check_successful_result(set_resp, set_action1_3, set_action1_2, set_action1_1)


def test_set_vlan_range_failed_clear(connectivity_flow):
    """Request contains one set VLAN range action that splits to sub actions.

    - execute clear with the last of the set VLAN sub actions, that fails
    - do not execute set VLAN
    - return failed result with last set sub VLAN action
    """
    connectivity_flow.is_clear_success = False
    set_ad1 = create_net_ad(
        set_vlan=True, vlan_id="11-13", mode=ConnectionModeEnum.TRUNK, uniq_id=False
    )
    request = create_request(set_ad1)
    set_ad1_1 = create_net_ad(set_vlan=True, vlan_id="11", uniq_id=False)
    set_ad1_2 = create_net_ad(set_vlan=True, vlan_id="12", uniq_id=False)
    set_ad1_3 = create_net_ad(set_vlan=True, vlan_id="13", uniq_id=False)

    resp_str = connectivity_flow.apply_connectivity(request)

    set_action1_1, set_action1_2, set_action1_3 = get_actions(
        connectivity_flow, set_ad1_1, set_ad1_2, set_ad1_3
    )
    expected_calls = [
        call.clear(set_action1_3, None),
    ]
    assert connectivity_flow.manager.mock_calls == expected_calls

    set_resp = get_one_result(resp_str)
    # limitation - error message show only the last sub action
    check_failed_result(set_resp, set_action1_3)


def test_set_vlan_range_failed_to_set(connectivity_flow):
    """Request contains one set VLAN range action that splits to sub actions.

    - execute clear with the last of the set VLAN sub actions
    - execute set VLAN for sub actions, 1st and 3rd fail, 2nd success
    - return one failed result with 2 errors
    """
    connectivity_flow.is_set_success = [False, True, False]
    set_ad1 = create_net_ad(
        set_vlan=True, vlan_id="11-13", mode=ConnectionModeEnum.TRUNK, uniq_id=False
    )
    request = create_request(set_ad1)
    set_ad1_1 = create_net_ad(set_vlan=True, vlan_id="11", uniq_id=False)
    set_ad1_2 = create_net_ad(set_vlan=True, vlan_id="12", uniq_id=False)
    set_ad1_3 = create_net_ad(set_vlan=True, vlan_id="13", uniq_id=False)

    resp_str = connectivity_flow.apply_connectivity(request)

    set_action1_1, set_action1_2, set_action1_3 = get_actions(
        connectivity_flow, set_ad1_1, set_ad1_2, set_ad1_3
    )
    expected_calls = [
        call.clear(set_action1_3, None),
        call.set_vlan(set_action1_1, None),
        call.set_vlan(set_action1_2, None),
        call.set_vlan(set_action1_3, None),
        call.clear(set_action1_1, None),
    ]
    assert connectivity_flow.manager.mock_calls == expected_calls

    set_resp = get_one_result(resp_str)
    check_failed_result(set_resp, set_action1_1, set_action1_3)
