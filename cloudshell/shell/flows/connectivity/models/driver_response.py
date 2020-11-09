from typing import List

from pydantic import BaseModel

from .connectivity_model import ConnectivityActionModel


class ConnectivityActionResult(BaseModel):
    actionId: str
    type: str  # noqa: A003
    updateInterface: str
    infoMessage: str = ""
    errorMessage: str = ""
    success: bool = True

    @staticmethod
    def _action_dict(action: ConnectivityActionModel):
        return {
            "actionId": action.action_id,
            "type": action.type.value,
            "updateInterface": action.action_target.name,
        }

    @classmethod
    def success_result(cls, action: ConnectivityActionModel, msg: str):
        return cls(**cls._action_dict(action), infoMessage=msg)

    @classmethod
    def fail_result(cls, action: ConnectivityActionModel, msg: str):
        return cls(**cls._action_dict(action), errorMessage=msg, success=False)


class DriverResponse(BaseModel):
    actionResults: List[ConnectivityActionResult]


class DriverResponseRoot(BaseModel):
    driverResponse: DriverResponse

    @classmethod
    def prepare_response(cls, action_results: List[ConnectivityActionResult]):
        return cls(driverResponse=DriverResponse(actionResults=action_results))
