from __future__ import annotations

import warnings
from abc import ABC, abstractmethod
from collections.abc import Collection
from copy import deepcopy
from typing import Any

from attrs import define

from cloudshell.shell.flows.connectivity.devices_flow import AbcDeviceConnectivityFlow
from cloudshell.shell.flows.connectivity.exceptions import ApplyConnectivityException
from cloudshell.shell.flows.connectivity.models.connectivity_model import (
    ConnectivityActionModel,
    ConnectivityTypeEnum,
)
from cloudshell.shell.flows.connectivity.models.driver_response import (
    ConnectivityActionResult,
)


@define
class AbstractConnectivityFlow(AbcDeviceConnectivityFlow, ABC):
    def __attrs_post_init__(self) -> None:
        depr_msg = (
            "This class is deprecated. Use AbcDeviceConnectivityFlow or "
            "AbcCloudProviderConnectivityFlow"
        )
        warnings.warn(depr_msg, DeprecationWarning, stacklevel=2)

    @abstractmethod
    def _set_vlan(self, action: ConnectivityActionModel) -> ConnectivityActionResult:
        # deprecated
        raise NotImplementedError()

    @abstractmethod
    def _remove_vlan(self, action: ConnectivityActionModel) -> ConnectivityActionResult:
        """Remove VLAN for the target.

        Target is defined by action_target.name for a port on networking device
        or custom_action_attrs.vm_uuid and custom_action_attrs.vnic for a VM.
        If connection_params.vlan_id is empty you should clear all VLANs for the target.
        """
        # deprecated
        raise NotImplementedError()

    def _validate_received_actions(
        self, actions: Collection[ConnectivityActionModel]
    ) -> None:
        # deprecated
        pass

    def set_vlan(self, action: ConnectivityActionModel, target: Any) -> str:
        result = self._set_vlan(action)
        if not result.success:
            raise ApplyConnectivityException(result.errorMessage)
        return result.updatedInterface

    def remove_vlan(self, action: ConnectivityActionModel, target: Any) -> str:
        result = self._remove_vlan(action)
        if not result.success:
            raise ApplyConnectivityException(result.errorMessage)
        return result.updatedInterface

    def validate_actions(self, actions: Collection[ConnectivityActionModel]) -> None:
        self._validate_received_actions(actions)

    def clear(self, action: ConnectivityActionModel, target: Any) -> str:
        """Executes before set VLAN actions and for rolling back failed."""
        a = deepcopy(action)
        a.connection_params.vlan_id = ""
        a.connection_params.vlan_service_attrs.vlan_id = ""
        a.type = ConnectivityTypeEnum.REMOVE_VLAN
        result = self._remove_vlan(a)
        if not result.success:
            raise ApplyConnectivityException(result.errorMessage)
        return result.updatedInterface
