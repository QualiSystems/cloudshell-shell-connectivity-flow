#!/usr/bin/python
# -*- coding: utf-8 -*-

from cloudshell.shell.flows.connectivity.exceptions import RequestValidatorException

APPLY_CONNECTIVITY_CHANGES_ACTION_REQUIRED_ATTRIBUTE_LIST = [
    "type",
    "actionId",
    ("connectionParams", "mode"),
    ("actionTarget", "fullAddress"),
]


def validate_request_action(action):
    """Validate action from the request json.

    Validating according to
        APPLY_CONNECTIVITY_CHANGES_ACTION_REQUIRED_ATTRIBUTE_LIST
    """
    is_fail = False
    fail_attribute = ""
    for class_attribute in APPLY_CONNECTIVITY_CHANGES_ACTION_REQUIRED_ATTRIBUTE_LIST:
        if type(class_attribute) is tuple:
            if not hasattr(action, class_attribute[0]):
                is_fail = True
                fail_attribute = class_attribute[0]
            if not hasattr(getattr(action, class_attribute[0]), class_attribute[1]):
                is_fail = True
                fail_attribute = class_attribute[1]
        else:
            if not hasattr(action, class_attribute):
                is_fail = True
                fail_attribute = class_attribute

    if is_fail:
        raise RequestValidatorException(
            "Mandatory field {0} is missing "
            "in ApplyConnectivityChanges request json".format(fail_attribute),
        )
