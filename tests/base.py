from __future__ import annotations

import json
from collections.abc import Collection
from typing import Any
from uuid import uuid4

from cloudshell.shell.flows.connectivity.helpers.dict_action_helpers import (
    get_val_from_list_attrs,
)
from cloudshell.shell.flows.connectivity.helpers.types import (
    ActionDict,
    ActionsAttributeDict,
    ActionTargetDict,
    ConnectionParamsDict,
)
from cloudshell.shell.flows.connectivity.helpers.vlan_helper import (
    VIRTUAL_NETWORK,
    VLAN_ID,
)
from cloudshell.shell.flows.connectivity.helpers.vnic_helpers import (
    INTERFACE,
    VM_UUID,
    VNIC_NAME,
    get_custom_action_attrs,
)
from cloudshell.shell.flows.connectivity.models.connectivity_model import (
    ConnectionModeEnum,
    ConnectivityActionModel,
    ConnectivityTypeEnum,
)
from cloudshell.shell.flows.connectivity.models.driver_response import (
    ConnectivityActionResult,
    DriverResponseRoot,
)

DEFAULT_CONNECTION_ID = str(uuid4())
DEFAULT_ACTION_ID = f"{DEFAULT_CONNECTION_ID}_{str(uuid4())}"
DEFAULT_VLAN_ID = "10"
DEFAULT_TARGET = "1/1/1"
DEFAULT_VM_NAME = "vm"
DEFAULT_VM_UUID = str(uuid4())


def create_net_ad(
    *,
    set_vlan: bool = True,
    vlan_id: str = DEFAULT_VLAN_ID,
    vlan_service_attrs_vlan_id: str | None = None,
    mode: ConnectionModeEnum = ConnectionModeEnum.ACCESS,
    target: str = DEFAULT_TARGET,
    uniq_id: bool = True,
    action_id: str | None = None,
) -> ActionDict:
    """Create Action Dict for networking devices."""
    return _create_ad(
        set_vlan=set_vlan,
        vlan_id=vlan_id,
        vlan_service_attrs_vlan_id=vlan_service_attrs_vlan_id,
        mode=mode,
        target=target,
        uniq_id=uniq_id,
        action_id=action_id,
    )


def create_cp_ad(
    *,
    set_vlan: bool = True,
    vlan_id: str = DEFAULT_VLAN_ID,
    vlan_service_attrs_vlan_id: str | None = None,
    mode: ConnectionModeEnum = ConnectionModeEnum.ACCESS,
    target: str = DEFAULT_VM_NAME,
    vm_uuid: str = DEFAULT_VM_UUID,
    vnic: str | None = None,
    virtual_network: str | None = None,
    existing_network: str | None = None,
    iface: str | None = None,
    uniq_id: bool = True,
    action_id: str | None = None,
) -> ActionDict:
    """Create Action Dict for Cloud Providers."""
    return _create_ad(
        set_vlan=set_vlan,
        vlan_id=vlan_id,
        vlan_service_attrs_vlan_id=vlan_service_attrs_vlan_id,
        mode=mode,
        target=target,
        virtual_network=virtual_network,
        existing_network=existing_network,
        iface=iface,
        vm_uuid=vm_uuid,
        vnic=vnic,
        uniq_id=uniq_id,
        action_id=action_id,
    )


def _create_ad(
    *,
    set_vlan: bool = True,
    vlan_id: str = DEFAULT_VLAN_ID,
    vlan_service_attrs_vlan_id: str | None = None,
    mode: ConnectionModeEnum = ConnectionModeEnum.ACCESS,
    target: str = DEFAULT_TARGET,
    virtual_network: str | None = None,
    existing_network: str | None = None,
    iface: str | None = None,
    vm_uuid: str | None = None,
    vnic: str | None = None,
    uniq_id: bool = True,
    action_id: str | None = None,
) -> ActionDict:
    assert not iface or not set_vlan, "iface can be specified only for removeVlan"

    # connection params
    # CloudShell sets VLAN ID to Virtual Network if it's empty
    virtual_network = virtual_network or vlan_id
    if vlan_service_attrs_vlan_id is None:
        vlan_service_attrs_vlan_id = vlan_id
    connection_params = ConnectionParamsDict(
        vlanId=vlan_id,
        mode=mode.value,
        vlanServiceAttributes=dict_to_action_attrs_dicts(
            {
                "QnQ": "False",
                "CTag": "",
                VLAN_ID: vlan_service_attrs_vlan_id,
                VIRTUAL_NETWORK: virtual_network,
                "Existing Network": existing_network,
            }
        ),
        type="foo",
    )

    # connector attributes
    connector_attrs = {}
    if iface:
        connector_attrs[INTERFACE] = iface

    # action target
    action_target = ActionTargetDict(fullName=target, fullAddress=target, type="foo")

    # custom action attributes
    custom_action_attrs = {}
    if vm_uuid:
        custom_action_attrs[VM_UUID] = vm_uuid
    if vnic:
        custom_action_attrs[VNIC_NAME] = vnic

    if action_id:
        a_id = action_id
        c_id = action_id.split("_")[0]
    elif uniq_id:
        c_id = str(uuid4())
        a_id = f"{c_id}_{str(uuid4())}"
    else:
        c_id, a_id = DEFAULT_CONNECTION_ID, DEFAULT_ACTION_ID
    connectivity_type = (
        ConnectivityTypeEnum.SET_VLAN if set_vlan else ConnectivityTypeEnum.REMOVE_VLAN
    ).value
    return ActionDict(
        connectionId=c_id,
        actionId=a_id,
        connectionParams=connection_params,
        connectorAttributes=dict_to_action_attrs_dicts(connector_attrs),
        actionTarget=action_target,
        customActionAttributes=dict_to_action_attrs_dicts(custom_action_attrs),
        type=connectivity_type,
    )


def dict_to_action_attrs_dicts(d: dict[str, str]) -> list[ActionsAttributeDict]:
    return [
        ActionsAttributeDict(
            attributeName=attr_name,
            attributeValue=attr_value,
            type="foo",
        )
        for attr_name, attr_value in d.items()
    ]


def create_request(*action_requests: ActionDict) -> str:
    return json.dumps({"driverRequest": {"actions": list(action_requests)}})


class TestConnectivityFlowHelper:
    def clear(self, action: ConnectivityActionModel, target: Any) -> str:
        return self._generic_change_vlan_fn(
            "clear", self.is_clear_success, action, target
        )

    def set_vlan(self, action: ConnectivityActionModel, target: Any) -> str:
        return self._generic_change_vlan_fn(
            "set_vlan", self.is_set_success, action, target
        )

    def remove_vlan(self, action: ConnectivityActionModel, target: Any) -> str:
        return self._generic_change_vlan_fn(
            "remove_vlan", self.is_remove_success, action, target
        )

    def _generic_change_vlan_fn(
        self,
        fn_name: str,
        is_success: bool | list[bool],
        action: ConnectivityActionModel,
        target: Any,
    ) -> str:
        if isinstance(is_success, list):
            is_success = is_success.pop(0)

        fn = getattr(self.manager, fn_name)
        fn(action, target)  # call mock

        if is_success is True:
            return ""
        else:
            raise Exception("fail")

    def parse_request(self, request: str) -> list[ConnectivityActionModel]:
        actions = super().parse_request(request)
        self.all_actions = actions
        return actions


def get_one_result(resp_str: str) -> ConnectivityActionResult:
    resp: DriverResponseRoot = DriverResponseRoot.parse_raw(resp_str)
    assert len(resp.driverResponse.actionResults) == 1, "Only one result is expected"
    return resp.driverResponse.actionResults[0]


def get_results(resp_str, *action_dicts: ActionDict) -> list[ConnectivityActionResult]:
    resp: DriverResponseRoot = DriverResponseRoot.parse_raw(resp_str)
    assert len(resp.driverResponse.actionResults) == len(action_dicts)
    results = []
    for action_dict in action_dicts:
        for result in resp.driverResponse.actionResults:
            if result.actionId == action_dict["actionId"]:
                results.append(result)
                break
        else:
            raise AssertionError(f"Result for {action_dict} not found")
    return results


def get_one_action(cf: TestConnectivityFlowHelper) -> ConnectivityActionModel:
    assert len(cf.all_actions) == 1, "Only one action is expected"
    return cf.all_actions[0]


def get_actions(
    cf: TestConnectivityFlowHelper, *action_dicts: ActionDict
) -> list[ConnectivityActionModel]:
    assert len(cf.all_actions) == len(action_dicts), f"{len(cf.all_actions)} exists"
    actions = []
    for action_dict in action_dicts:
        for action in cf.all_actions:
            a_id = action.action_id
            ad_id = action_dict["actionId"]
            a_vlan = action.connection_params.vlan_id
            ad_vlan = action_dict["connectionParams"]["vlanId"]
            a_vnic = action.custom_action_attrs.vnic
            try:
                ad_vnic = get_val_from_list_attrs(
                    get_custom_action_attrs(action_dict), VNIC_NAME
                )
            except KeyError:
                ad_vnic = a_vnic = None

            if a_id == ad_id and a_vlan == ad_vlan and a_vnic == ad_vnic:
                actions.append(action)
                break
        else:
            raise AssertionError(f"Action for {action_dict} not found")
    return actions


def check_successful_result(
    resp: ConnectivityActionResult,
    *actions: ConnectivityActionModel,
    targets: Collection[str] | None = None,
) -> None:
    assert resp.success
    assert resp.errorMessage == ""

    types = {action.type for action in actions}
    assert len(types) == 1, "All actions should have the same type"
    type_ = types.pop().value  # setVlan or removeVlan

    if targets:
        assert sorted(resp.updatedInterface.split(";")) == sorted(targets)
    else:
        assert resp.updatedInterface == actions[0].action_target.name

    expected_msgs = []
    for action in actions:
        vlan = action.connection_params.vlan_id
        expected_msgs.append(f"{type_} {vlan} applied successfully")

    msgs = resp.infoMessage.splitlines()
    assert sorted(msgs) == sorted(expected_msgs)


def check_failed_result(
    resp: ConnectivityActionResult, *actions: ConnectivityActionModel
) -> None:
    assert resp.success is False
    assert resp.infoMessage == ""

    types = {action.type for action in actions}
    assert len(types) == 1, "All actions should have the same type"
    type_ = types.pop().value  # setVlan or removeVlan

    assert resp.updatedInterface == actions[0].action_target.name

    target = actions[0].action_target.name
    expected_msgs = []
    for action in actions:
        vlan = action.connection_params.vlan_id
        expected_msgs.append(f"Failed to {type_} {vlan} for {target}. Error: fail")

    msgs = resp.errorMessage.splitlines()
    assert sorted(msgs) == sorted(expected_msgs)
