from __future__ import annotations

from pydantic import BaseModel
from typing_extensions import Self

from .connectivity_model import ConnectivityActionModel


class ConnectivityActionResult(BaseModel):
    actionId: str  # noqa: N815
    type: str  # noqa: A003
    updatedInterface: str  # noqa: N815
    infoMessage: str = ""  # noqa: N815
    errorMessage: str = ""  # noqa: N815
    success: bool = True

    @staticmethod
    def _action_dict(action: ConnectivityActionModel) -> dict[str, str]:
        return {
            "actionId": action.action_id,
            "type": action.type.value,
            "updatedInterface": action.action_target.name,
        }

    @classmethod
    def success_result(cls, action: ConnectivityActionModel, msg: str) -> Self:
        return cls(**cls._action_dict(action), infoMessage=msg, success=True)

    @classmethod
    def success_result_vm(
        cls, action: ConnectivityActionModel, msg: str, mac_address: str
    ) -> Self:
        inst = cls.success_result(action, msg)
        inst.updatedInterface = mac_address
        return inst

    @classmethod
    def fail_result(cls, action: ConnectivityActionModel, msg: str) -> Self:
        return cls(**cls._action_dict(action), errorMessage=msg, success=False)

    @classmethod
    def skip_result(
        cls, action: ConnectivityActionModel, msg: str | None = None
    ) -> Self:
        if msg is None:
            msg = "Another action failed. Skipping this action"
        return cls.fail_result(action, msg)


class DriverResponse(BaseModel):
    actionResults: list[ConnectivityActionResult]  # noqa: N815


class DriverResponseRoot(BaseModel):
    driverResponse: DriverResponse  # noqa: N815

    @classmethod
    def prepare_response(cls, action_results: list[ConnectivityActionResult]) -> Self:
        return cls(driverResponse=DriverResponse(actionResults=action_results))
