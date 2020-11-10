from __future__ import annotations

import json
from enum import Enum
from functools import partial
from itertools import chain

from pydantic import BaseModel, Field, validator

from cloudshell.shell.flows.connectivity.helpers.vlan_helper import (
    iterate_dict_actions_by_vlan_range,
)


class ConnectivityTypeEnum(Enum):
    SET_VLAN = "setVlan"
    REMOVE_VLAN = "removeVlan"


class ConnectionModeEnum(Enum):
    ACCESS = "Access"
    TRUNK = "Trunk"


def list_attrs_to_dict(list_attrs: list[dict[str, str]]) -> dict[str, str]:
    return {attr["attributeName"]: attr["attributeValue"] for attr in list_attrs}


class VlanServiceModel(BaseModel):
    qnq: bool = Field(..., alias="QnQ")
    ctag: str = Field(..., alias="CTag")


class ConnectionParamsModel(BaseModel):
    vlan_id: str = Field(..., alias="vlanId")
    mode: ConnectionModeEnum
    type: str  # noqa: A003
    vlan_service_attrs: VlanServiceModel = Field(..., alias="vlanServiceAttributes")

    # validators
    _list_attrs_to_dict = validator("vlan_service_attrs", allow_reuse=True, pre=True)(
        list_attrs_to_dict
    )


class ConnectorAttributesModel(BaseModel):
    interface: str = Field("", alias="Interface")


class ActionTargetModel(BaseModel):
    name: str = Field(..., alias="fullName")
    address: str = Field(..., alias="fullAddress")


class CustomActionAttrsModel(BaseModel):
    vm_uuid: str = Field("", alias="VM_UUID")
    vnic: str = Field("", alias="Vnic Name")


class ConnectivityActionModel(BaseModel):
    connection_id: str = Field(..., alias="connectionId")
    connection_params: ConnectionParamsModel = Field(..., alias="connectionParams")
    connector_attrs: ConnectorAttributesModel = Field(..., alias="connectorAttributes")
    action_target: ActionTargetModel = Field(..., alias="actionTarget")
    custom_action_attrs: CustomActionAttrsModel = Field(
        ..., alias="customActionAttributes"
    )
    action_id: str = Field(..., alias="actionId")
    type: ConnectivityTypeEnum  # noqa: A003

    # validators
    _list_attrs_to_dict = validator(
        "connector_attrs", "custom_action_attrs", allow_reuse=True, pre=True
    )(list_attrs_to_dict)


def get_actions_from_request(
    request: str,
    model: type[ConnectivityActionModel],
    is_vlan_range_supported: bool,
    is_multi_vlan_supported: bool,
) -> list[ConnectivityActionModel]:
    dict_actions = json.loads(request)["driverRequest"]["actions"]
    parse_partial_fn = partial(
        iterate_dict_actions_by_vlan_range,
        is_vlan_range_supported=is_vlan_range_supported,
        is_multi_vlan_supported=is_multi_vlan_supported,
    )
    return [model.parse_obj(da) for da in chain(*map(parse_partial_fn, dict_actions))]
