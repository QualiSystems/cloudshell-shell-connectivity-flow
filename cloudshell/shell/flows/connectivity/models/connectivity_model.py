from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, root_validator


class ConnectivityTypeEnum(Enum):
    SET_VLAN = "setVlan"
    REMOVE_VLAN = "removeVlan"


class ConnectionModeEnum(Enum):
    ACCESS = "Access"
    TRUNK = "Trunk"


def _list_attrs_to_dict(list_attrs: List[Dict[str, str]]) -> Dict[str, str]:
    return {attr["attributeName"]: attr["attributeValue"] for attr in list_attrs}


class ConnectionParamsModel(BaseModel):
    vlan_id: int = Field(..., alias="vlanId")
    mode: ConnectionModeEnum
    vlan_service_attrs: Dict[str, str] = Field(..., alias="vlanServiceAttributes")
    qnq: bool
    ctag: str
    type: str  # noqa: A003

    @root_validator(pre=True)
    def _set_qnq_and_ctag_and_vlan_attrs(cls, values):
        vlan_service_attrs = _list_attrs_to_dict(values["vlanServiceAttributes"])
        qnq = vlan_service_attrs["QnQ"]
        ctag = vlan_service_attrs["CTag"]
        values.update(
            {"qnq": qnq, "ctag": ctag, "vlanServiceAttributes": vlan_service_attrs}
        )
        return values


class ActionTargetModel(BaseModel):
    name: str = Field(..., alias="fullName")
    address: str = Field(..., alias="fullAddress")


class ConnectivityActionModel(BaseModel):
    connection_id: str = Field(..., alias="connectionId")
    connection_params: ConnectionParamsModel = Field(..., alias="connectionParams")
    connector_attrs: Dict[str, str] = Field({}, alias="connectorAttributes")
    action_target: ActionTargetModel = Field(..., alias="actionTarget")
    custom_action_attrs: Dict[str, str] = Field(..., alias="customActionAttributes")
    action_id: str = Field(..., alias="actionId")
    type: ConnectivityTypeEnum  # noqa: A003
    vm_uid: Optional[str]

    @root_validator(pre=True)
    def _set_connection_and_custom_actions_attrs(cls, values):
        connector_attrs = _list_attrs_to_dict(values["connectorAttributes"])
        custom_action_attrs = _list_attrs_to_dict(values["customActionAttributes"])
        vm_uid = custom_action_attrs.get("VM_UUID")
        values.update(
            {
                "connectorAttributes": connector_attrs,
                "customActionAttributes": custom_action_attrs,
                "vm_uid": vm_uid,
            }
        )
        return values
