#!/usr/bin/python
# -*- coding: utf-8 -*-

import traceback
from abc import abstractmethod
from collections import defaultdict
from threading import Thread, current_thread

import jsonpickle
from cloudshell.logging.utils.decorators import command_logging

from cloudshell.shell.flows.connectivity.exceptions import ApplyConnectivityException
from cloudshell.shell.flows.connectivity.helpers.request_validation import (
    validate_request_action,
)
from cloudshell.shell.flows.connectivity.helpers.utils import JsonRequestDeserializer
from cloudshell.shell.flows.connectivity.helpers.vlan_handler import VLANHandler
from cloudshell.shell.flows.connectivity.interfaces import ConnectivityFlowInterface
from cloudshell.shell.flows.connectivity.models.connectivity_result import (
    ConnectivityErrorResponse,
    ConnectivitySuccessResponse,
)
from cloudshell.shell.flows.connectivity.models.driver_response import DriverResponse
from cloudshell.shell.flows.connectivity.models.driver_response_root import (
    DriverResponseRoot,
)
from cloudshell.shell.flows.connectivity.utils import get_vm_uid


class AbstractConnectivityFlow(ConnectivityFlowInterface):
    # Indicates if VLAN ranges are supported like "120-130"
    IS_VLAN_RANGE_SUPPORTED = True
    # Indicates if device supports comma separated VLAN request like "45, 65, 120-130"
    IS_MULTI_VLAN_SUPPORTED = True

    def __init__(self, logger):
        """Abstract connectivity flow.

        :param logging.Logger logger:
        """
        self._logger = logger
        self.result = defaultdict(list)

    @abstractmethod
    def _add_vlan_flow(self, vlan_range, port_mode, full_name, qnq, c_tag, vm_uid):
        """Add VLAN, has to be implemented."""
        pass

    @abstractmethod
    def _remove_vlan_flow(self, vlan_range, full_name, port_mode, vm_uid):
        """Remove VLAN, has to be implemented."""
        pass

    @abstractmethod
    def _remove_all_vlan_flow(self, full_name, vm_uid):
        """Remove VLAN, has to be implemented."""
        pass

    @command_logging
    def apply_connectivity_changes(self, request):
        """Handle apply connectivity changes request json.

        Trigger add or remove vlan methods, get responce from them and
            create json response

        :param request: json with all required action to configure or remove vlans
            from certain port
        :return Serialized DriverResponseRoot to json
        :rtype json
        """
        if request is None or request == "":
            raise ApplyConnectivityException("Request is None or empty")

        holder = JsonRequestDeserializer(jsonpickle.decode(request))

        if not holder or not hasattr(holder, "driverRequest"):
            raise ApplyConnectivityException("Deserialized request is None or empty")

        driver_response = DriverResponse()
        add_vlan_thread_list = []
        remove_vlan_thread_list = []
        remove_all_vlan_args = set()
        driver_response_root = DriverResponseRoot()
        vlan_handler = VLANHandler(
            is_vlan_range_supported=self.IS_VLAN_RANGE_SUPPORTED,
            is_multi_vlan_supported=self.IS_MULTI_VLAN_SUPPORTED,
        )

        for action in holder.driverRequest.actions:
            self._logger.info("Action: ", action.__dict__)
            validate_request_action(action)

            action_id = action.actionId
            full_name = action.actionTarget.fullName
            port_mode = action.connectionParams.mode.lower()
            vm_uid = get_vm_uid(action)

            if action.type == "setVlan":
                qnq = False
                ctag = ""
                for attribute in action.connectionParams.vlanServiceAttributes:
                    if (
                        attribute.attributeName.lower() == "qnq"
                        and attribute.attributeValue.lower() == "true"
                    ):
                        qnq = True
                    if attribute.attributeName.lower() == "ctag":
                        ctag = attribute.attributeValue
                remove_all_vlan_args.add((full_name, vm_uid))
                for vlan_id in vlan_handler.get_vlan_list(
                    action.connectionParams.vlanId
                ):
                    add_vlan_thread = Thread(
                        target=self._add_vlan_executor,
                        name=action_id,
                        args=(vlan_id, full_name, port_mode, qnq, ctag, vm_uid),
                    )
                    add_vlan_thread_list.append(add_vlan_thread)
            elif action.type == "removeVlan":
                for vlan_id in vlan_handler.get_vlan_list(
                    action.connectionParams.vlanId
                ):
                    remove_vlan_thread = Thread(
                        target=self._remove_vlan_executor,
                        name=action_id,
                        args=(vlan_id, full_name, port_mode, vm_uid),
                    )
                    remove_vlan_thread_list.append(remove_vlan_thread)
            else:
                self._logger.warning(
                    "Undefined action type determined '{}': {}".format(
                        action.type, action.__dict__
                    )
                )
                continue

        self._remove_all_vlan_in_threads(remove_all_vlan_args)

        # Start all created remove_vlan_threads
        for thread in remove_vlan_thread_list:
            thread.start()

        # Join all remove_vlan_threads.
        # Main thread will wait completion of all remove_vlan_thread
        for thread in remove_vlan_thread_list:
            thread.join()

        # Start all created add_vlan_threads
        for thread in add_vlan_thread_list:
            thread.start()

        # Join all add_vlan_threads.
        # Main thread will wait completion of all add_vlan_thread
        for thread in add_vlan_thread_list:
            thread.join()

        request_result = []
        for action in holder.driverRequest.actions:
            result_statuses, message = zip(*self.result.get(action.actionId))
            if all(result_statuses):
                action_result = ConnectivitySuccessResponse(
                    action,
                    "Add Vlan {vlan} configuration successfully completed".format(
                        vlan=action.connectionParams.vlanId
                    ),
                )
            else:
                message_details = "\n\t".join(message)
                action_result = ConnectivityErrorResponse(
                    action,
                    "Add Vlan {vlan} configuration failed."
                    "\nAdd Vlan configuration details:\n{message_details}".format(
                        vlan=action.connectionParams.vlanId,
                        message_details=message_details,
                    ),
                )
            request_result.append(action_result)

        driver_response.actionResults = request_result
        driver_response_root.driverResponse = driver_response
        return str(
            jsonpickle.encode(driver_response_root, unpicklable=False)
        )  # .replace("[true]", "true")

    def _add_vlan_executor(self, vlan_id, full_name, port_mode, qnq, c_tag, vm_uid):
        """Run flow to add VLAN(s) to interface.

        :param vlan_id: Already validated number of VLAN(s)
        :param full_name: Full interface name. Example: 2950/Chassis 0/FastEthernet0-23
        :param port_mode: port mode type. Should be trunk or access
        :param qnq:
        :param c_tag:
        """
        try:
            action_result = self._add_vlan_flow(
                vlan_range=vlan_id,
                port_mode=port_mode,
                full_name=full_name,
                qnq=qnq,
                c_tag=c_tag,
                vm_uid=vm_uid,
            )
            self.result[current_thread().name].append((True, action_result))
        except Exception as e:
            emsg = "Failed to configure vlan {} for interface {}".format(
                vlan_id, full_name
            )
            if vm_uid is not None:
                emsg += " on VM id {}".format(vm_uid)
            self._logger.error(emsg)
            self._logger.error(traceback.format_exc())
            self.result[current_thread().name].append((False, str(e)))

    def _remove_vlan_executor(self, vlan_id, full_name, port_mode, vm_uid):
        """Run flow to remove VLAN(s) from interface.

        :param vlan_id: Already validated number of VLAN(s)
        :param full_name: Full interface name. Example: 2950/Chassis 0/FastEthernet0-23
        :param port_mode: port mode type. Should be trunk or access
        """
        try:

            action_result = self._remove_vlan_flow(
                vlan_range=vlan_id,
                full_name=full_name,
                port_mode=port_mode,
                vm_uid=vm_uid,
            )
            self.result[current_thread().name].append((True, action_result))
        except Exception as e:
            self._logger.error(traceback.format_exc())
            self.result[current_thread().name].append((False, str(e)))

    def _remove_all_vlan_in_threads(self, vlan_args):
        threads = [
            Thread(target=self._remove_all_vlan_flow, args=args) for args in vlan_args
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
