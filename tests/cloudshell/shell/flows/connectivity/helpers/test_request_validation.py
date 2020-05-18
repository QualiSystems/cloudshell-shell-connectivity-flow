#!/usr/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase

from cloudshell.shell.flows.connectivity.helpers.request_validation import (
    validate_request_action,
)


class TestJsonRequestDeserializer(TestCase):
    def test_validate_request_action_no_attr(self):
        """Check that method will raise an exception if required attr missed."""
        with self.assertRaisesRegexp(
            Exception,
            "Mandatory field actionId is missing in ApplyConnectivityChanges "
            "request json",
        ):

            class Action(object):
                type = ""  # noqa

                class connectionParams(object):
                    mode = ""

                class actionTarget(object):
                    fullAddress = ""

            validate_request_action(action=Action())

    def test_validate_request_action_no_nested_obj(self):
        """Check that method will raise an exception if required attr missed."""
        with self.assertRaisesRegexp(
            Exception, "'Action' object has no attribute 'connectionParams'"
        ):

            class Action(object):
                type = ""  # noqa
                actionId = ""

                class actionTarget(object):
                    fullAddress = ""

            validate_request_action(action=Action())

    def test_validate_request_action_no_attr_on_nested_obj(self):
        """Check that method will raise an exception if required attr missed."""
        with self.assertRaisesRegexp(
            Exception,
            "Mandatory field mode is missing in ApplyConnectivityChanges "
            "request json",
        ):

            class Action(object):
                type = ""  # noqa
                actionId = ""

                class connectionParams(object):
                    pass

                class actionTarget(object):
                    fullAddress = ""

            validate_request_action(action=Action())
