#!/usr/bin/python
# -*- coding: utf-8 -*-


class ConnectivityActionResult(object):
    def __init__(self, action):
        self.actionId = action.actionId
        self.type = action.type
        self.updatedInterface = action.actionTarget.fullName
        self.infoMessage = None
        self.errorMessage = None
        self.success = True


class ConnectivitySuccessResponse(ConnectivityActionResult):
    def __init__(self, action, result_string):
        ConnectivityActionResult.__init__(self, action)
        self.infoMessage = result_string


class ConnectivityErrorResponse(ConnectivityActionResult):
    def __init__(self, action, error_string):
        ConnectivityActionResult.__init__(self, action)
        self.errorMessage = error_string
        self.success = False
