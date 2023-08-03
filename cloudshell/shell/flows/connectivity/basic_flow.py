from __future__ import annotations

import warnings
from abc import ABC, abstractmethod
from collections.abc import Collection
from typing import Any

from attrs import define

from cloudshell.shell.flows.connectivity.devices_flow import AbcDeviceConnectivityFlow
from cloudshell.shell.flows.connectivity.models.connectivity_model import (
    ConnectivityActionModel,
)
from cloudshell.shell.flows.connectivity.models.driver_response import (
    ConnectivityActionResult,
)


@define
class AbstractConnectivityFlow(AbcDeviceConnectivityFlow, ABC):
    def __attrs_post_init__(self):
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

    def set_vlan(
        self, action: ConnectivityActionModel, target: Any
    ) -> ConnectivityActionResult:
        return self._set_vlan(action)

    def remove_vlan(
        self, action: ConnectivityActionModel, target: Any
    ) -> ConnectivityActionResult:
        return self._remove_vlan(action)

    def validate_actions(self, actions: Collection[ConnectivityActionModel]) -> None:
        self._validate_received_actions(actions)
