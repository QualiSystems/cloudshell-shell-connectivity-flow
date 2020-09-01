#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from unittest import TestCase

from cloudshell.shell.flows.connectivity.exceptions import VLANHandlerException
from cloudshell.shell.flows.connectivity.helpers.vlan_handler import VLANHandler

if sys.version_info >= (3, 0):
    from unittest import mock
else:
    import mock


class TestJsonRequestDeserializer(TestCase):
    def setUp(self):
        self.vlan_handler = VLANHandler()

    def test__sort_vlans_only(self):
        """Check that method will return list of sorted VLANs.

        It will sort list of VLANs (not VLAN Ranges)
        """
        vlan_list = ["5", "33", "11", "2"]
        # act
        self.vlan_handler.is_vlan_range_supported = False
        result = self.vlan_handler._sort_vlans(vlan_list=vlan_list)
        # verify
        self.assertEqual(result, ["2", "5", "11", "33"])

    def test__sort_vlans_with_ranges(self):
        """Check that method will return list of sorted VLANs.

        It will sort list of VLANs and VLAN Ranges)
        """
        vlan_list = ["5", "11-30", "33", "7"]
        # act
        self.vlan_handler.is_vlan_range_supported = True
        result = self.vlan_handler._sort_vlans(vlan_list=vlan_list)
        # verify
        self.assertEqual(result, ["5", "7", "11-30", "33"])

    def test_get_vlan_list(self):
        """Check that method will return list of valid VLANs."""
        vlan_str = "10-15,19,21-23"
        # act
        self.vlan_handler.is_multi_vlan_supported = False
        result = self.vlan_handler.get_vlan_list(vlan_str=vlan_str)
        # verify
        self.assertEqual(result, ["10-15", "19", "21-23"])

    def test_get_vlan_list_as_list_vlan_range_range_is_not_supported(self):
        """Check that method will return list with VLANs.

        It will create VLANs between the given range and change start/end if needed
        """
        self.vlan_handler.is_vlan_range_supported = False
        self.vlan_handler.is_multi_vlan_supported = False
        vlan_str = "12-10"
        # act
        result = self.vlan_handler.get_vlan_list(vlan_str=vlan_str)
        # verify
        self.assertEqual(result, ["10", "11", "12"])

    def test_get_vlan_list_as_str_vlan_range_range_is_not_supported(self):
        """Check that method will return string with VLANs.

        It will create VLANs between the given range and change start/end if needed
        """
        self.vlan_handler.is_vlan_range_supported = False
        self.vlan_handler.is_multi_vlan_supported = True
        vlan_str = "12-10"
        # act
        result = self.vlan_handler.get_vlan_list(vlan_str=vlan_str)
        # verify
        self.assertEqual(result, ["10,11,12"])

    def test_get_vlan_list_invalid_vlan_number(self):
        """Check that method will raise Exception if VLAN number is not valid."""
        self.vlan_handler.is_multi_vlan_supported = True
        self.vlan_handler.validate_vlan_number = mock.MagicMock(return_value=False)
        vlan_str = "5000"
        # act # verify
        with self.assertRaisesRegexp(
            VLANHandlerException,
            "Wrong VLAN detected {vlan_str}".format(vlan_str=vlan_str),
        ):
            self.vlan_handler.get_vlan_list(vlan_str=vlan_str)

    def test_get_vlan_list_invalid_vlan_range(self):
        """Check that method will raise Exception if VLAN range is not valid."""
        self.vlan_handler.is_vlan_range_supported = True
        self.vlan_handler.validate_vlan_range = mock.MagicMock(return_value=False)
        vlan_str = "5000-5005"
        # act # verify
        with self.assertRaisesRegexp(VLANHandlerException, "Wrong VLAN detected 5000"):
            self.vlan_handler.get_vlan_list(vlan_str=vlan_str)

    def test_get_vlan_list_invalid_vlan_range_range_is_not_supported(self):
        """Check that method will raise Exception if VLAN range is not valid."""
        self.vlan_handler.is_vlan_range_supported = False
        self.vlan_handler.validate_vlan_number = mock.MagicMock(return_value=False)
        vlan_str = "5000-5005"
        # act
        with self.assertRaisesRegexp(VLANHandlerException, "Wrong VLAN detected 5000"):
            self.vlan_handler.get_vlan_list(vlan_str=vlan_str)
