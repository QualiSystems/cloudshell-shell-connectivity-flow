from __future__ import annotations

from typing import TypedDict


class ActionDict(TypedDict):
    connectionId: str
    connectionParams: ConnectionParamsDict
    connectorAttributes: list[ActionsAttributeDict]
    actionTarget: ActionTargetDict
    customActionAttributes: list[ActionsAttributeDict]
    actionId: str
    type: str  # noqa: A003


class ConnectionParamsDict(TypedDict):
    vlanId: str
    mode: str
    vlanServiceAttributes: list[ActionsAttributeDict]
    type: str  # noqa: A003


class ActionTargetDict(TypedDict):
    fullName: str
    fullAddress: str
    type: str  # noqa: A003


class ActionsAttributeDict(TypedDict):
    attributeName: str
    attributeValue: str
    type: str  # noqa: A003
