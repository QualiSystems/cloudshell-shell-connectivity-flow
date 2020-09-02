#!/usr/bin/python
# -*- coding: utf-8 -*-

from cloudshell.shell.flows.connectivity.exceptions import VLANHandlerException


class VLANHandler:
    def __init__(self, is_vlan_range_supported=True, is_multi_vlan_supported=True):
        self.is_vlan_range_supported = is_vlan_range_supported
        self.is_multi_vlan_supported = is_multi_vlan_supported

    @staticmethod
    def _validate_vlan_number(number):
        try:
            number = int(number)
        except ValueError:
            raise VLANHandlerException("VLAN {} isn't a integer".format(number))
        if number > 4094 or number < 1:
            raise VLANHandlerException("Wrong VLAN detected {}".format(number))

    def _validate_vlan_range(self, vlan_range):
        for vlan in vlan_range.split(","):
            if "-" in vlan:
                for vlan_range_border in vlan.split("-"):
                    self._validate_vlan_number(vlan_range_border)
            else:
                self._validate_vlan_number(vlan)

    def _sort_vlans(self, vlan_list):
        """Sort VLAN list.

        :param vlan_list:
        :return list of sorted VLANs/VLAN Ranges or Exception
        """
        if not self.is_vlan_range_supported:
            return sorted(vlan_list, key=int)
        else:
            temp = []
            for vlan in vlan_list:
                if "-" in str(vlan):
                    temp.append(tuple(map(int, vlan.split("-"))))
                else:
                    temp.append((int(vlan), int(vlan)))

            res = []
            for vlan in sorted(temp):
                if vlan[0] == vlan[1]:
                    res.append(str(vlan[0]))
                else:
                    res.append("{}-{}".format(vlan[0], vlan[1]))

            return res

    def get_vlan_list(self, vlan_str):
        """Get VLAN list from input string.

        :param vlan_str:
        :return list of VLANs or Exception
        """
        result = set()
        for splitted_vlan in vlan_str.split(","):
            if "-" not in splitted_vlan:
                self._validate_vlan_number(splitted_vlan)
                result.add(int(splitted_vlan))
            else:
                splitted_vlan = splitted_vlan.strip()
                if self.is_vlan_range_supported:
                    self._validate_vlan_range(splitted_vlan)
                    result.add(splitted_vlan)
                else:
                    start, end = map(int, splitted_vlan.split("-"))
                    self._validate_vlan_number(start)
                    self._validate_vlan_number(end)
                    if start > end:
                        start, end = end, start
                    result.update(range(start, end + 1))
        vlan_range_list = self._sort_vlans(map(str, result))
        if self.is_multi_vlan_supported:
            return [",".join(vlan_range_list)]
        else:
            return vlan_range_list
