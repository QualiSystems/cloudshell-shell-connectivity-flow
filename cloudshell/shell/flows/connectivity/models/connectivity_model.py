from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, constr, validator


class ConnectivityTypeEnum(Enum):
    SET_VLAN = "setVlan"
    REMOVE_VLAN = "removeVlan"


class ConnectionModeEnum(Enum):
    ACCESS = "Access"
    TRUNK = "Trunk"


def list_attrs_to_dict(list_attrs: List[Dict[str, str]]) -> Dict[str, str]:
    return {attr["attributeName"]: attr["attributeValue"] for attr in list_attrs}


class VlanServiceModel(BaseModel):
    qnq: bool = Field(..., alias="QnQ")
    ctag: str = Field(..., alias="CTag")
    vlan_id: str = Field(..., alias="VLAN ID")
    virtual_network: Optional[str] = Field("", alias="Virtual Network")
    promiscuous_mode: Optional[bool] = Field(None, alias="Promiscuous Mode")
    forged_transmits: Optional[bool] = Field(None, alias="Forged Transmits")
    mac_changes: Optional[bool] = Field(None, alias="MAC Address Changes")
    switch_name: Optional[str] = Field(None, alias="Switch Name")


class ConnectionParamsModel(BaseModel):
    # if Virtual Network set vlanId will be overwritten
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
    vnic: constr(strip_whitespace=True) = Field("", alias="Vnic Name")


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
