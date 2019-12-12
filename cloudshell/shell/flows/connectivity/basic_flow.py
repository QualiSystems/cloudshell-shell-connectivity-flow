import traceback
from abc import abstractmethod
from collections import defaultdict
from threading import Thread, current_thread

import jsonpickle
from cloudshell.logging.utils.decorators import command_logging

from cloudshell.shell.flows.connectivity.driver_response import DriverResponse
from cloudshell.shell.flows.connectivity.driver_response_root import DriverResponseRoot
from cloudshell.shell.flows.connectivity.interfaces import ConnectivityFlowInterface
from cloudshell.shell.flows.connectivity.utils import JsonRequestDeserializer


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


class AbstractConnectivityFlow(ConnectivityFlowInterface):
    IS_VLAN_RANGE_SUPPORTED = True
    APPLY_CONNECTIVITY_CHANGES_ACTION_REQUIRED_ATTRIBUTE_LIST = [
        "type",
        "actionId",
        ("connectionParams", "mode"),
        ("actionTarget", "fullAddress"),
    ]

    def __init__(self, logger):
        """Abstract connectivity flow.

        :param logging.Logger logger:
        """
        self._logger = logger
        self.result = defaultdict(list)

    @abstractmethod
    def _add_vlan_flow(self, vlan_range, port_mode, port_name, qnq, c_tag):
        """Add VLAN, has to be implemented."""
        pass

    @abstractmethod
    def _remove_vlan_flow(self, vlan_range, port_name, port_mode):
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
            raise Exception(self.__class__.__name__, "request is None or empty")

        holder = JsonRequestDeserializer(jsonpickle.decode(request))

        if not holder or not hasattr(holder, "driverRequest"):
            raise Exception(
                self.__class__.__name__, "Deserialized request is None or empty"
            )

        driver_response = DriverResponse()
        add_vlan_thread_list = []
        remove_vlan_thread_list = []
        driver_response_root = DriverResponseRoot()

        for action in holder.driverRequest.actions:
            self._logger.info("Action: ", action.__dict__)
            self._validate_request_action(action)

            action_id = action.actionId
            full_name = action.actionTarget.fullName
            port_mode = action.connectionParams.mode.lower()

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

                for vlan_id in self._get_vlan_list(action.connectionParams.vlanId):
                    add_vlan_thread = Thread(
                        target=self._add_vlan_executor,
                        name=action_id,
                        args=(vlan_id, full_name, port_mode, qnq, ctag),
                    )
                    add_vlan_thread_list.append(add_vlan_thread)
            elif action.type == "removeVlan":
                for vlan_id in self._get_vlan_list(action.connectionParams.vlanId):
                    remove_vlan_thread = Thread(
                        target=self._remove_vlan_executor,
                        name=action_id,
                        args=(vlan_id, full_name, port_mode),
                    )
                    remove_vlan_thread_list.append(remove_vlan_thread)
            else:
                self._logger.warning(
                    "Undefined action type determined '{}': {}".format(
                        action.type, action.__dict__
                    )
                )
                continue

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

    def _validate_request_action(self, action):
        """Validate action from the request json.

        Validating according to
            APPLY_CONNECTIVITY_CHANGES_ACTION_REQUIRED_ATTRIBUTE_LIST
        """
        is_fail = False
        fail_attribute = ""
        for (
            class_attribute
        ) in self.APPLY_CONNECTIVITY_CHANGES_ACTION_REQUIRED_ATTRIBUTE_LIST:
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
            raise Exception(
                self.__class__.__name__,
                "Mandatory field {0} is missing in ApplyConnectivityChanges request "
                "json".format(fail_attribute),
            )

    @staticmethod
    def _validate_vlan_number(number):
        try:
            if int(number) > 4000 or int(number) < 1:
                return False
        except ValueError:
            return False
        return True

    def _validate_vlan_range(self, vlan_range):
        result = None
        for vlan in vlan_range.split(","):
            if "-" in vlan:
                for vlan_range_border in vlan.split("-"):
                    result = self._validate_vlan_number(vlan_range_border)
            else:
                result = self._validate_vlan_number(vlan)
            if not result:
                return False
        return True

    def _get_vlan_list(self, vlan_str):
        """Get VLAN list from input string.

        :param vlan_str:
        :return list of VLANs or Exception
        """
        result = set()
        for splitted_vlan in vlan_str.split(","):
            if "-" not in splitted_vlan:
                if self._validate_vlan_number(splitted_vlan):
                    result.add(int(splitted_vlan))
                else:
                    raise Exception(
                        self.__class__.__name__,
                        "Wrong VLAN number detected {}".format(splitted_vlan),
                    )
            else:
                if self.IS_VLAN_RANGE_SUPPORTED:
                    if self._validate_vlan_range(splitted_vlan):
                        result.add(splitted_vlan)
                    else:
                        raise Exception(
                            self.__class__.__name__,
                            "Wrong VLANs range detected {}".format(vlan_str),
                        )
                else:
                    start, end = map(int, splitted_vlan.split("-"))
                    if self._validate_vlan_number(start) and self._validate_vlan_number(
                        end
                    ):
                        if start > end:
                            start, end = end, start
                        for vlan in range(start, end + 1):
                            result.add(vlan)
                    else:
                        raise Exception(
                            self.__class__.__name__,
                            "Wrong VLANs range detected {}".format(vlan_str),
                        )

        return list(map(str, result))

    def _add_vlan_executor(self, vlan_id, full_name, port_mode, qnq, c_tag):
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
                port_name=full_name,
                qnq=qnq,
                c_tag=c_tag,
            )
            self.result[current_thread().name].append((True, action_result))
        except Exception as e:
            self._logger.error(traceback.format_exc())
            self.result[current_thread().name].append((False, str(e)))

    def _remove_vlan_executor(self, vlan_id, full_name, port_mode):
        """Run flow to remove VLAN(s) from interface.

        :param vlan_id: Already validated number of VLAN(s)
        :param full_name: Full interface name. Example: 2950/Chassis 0/FastEthernet0-23
        :param port_mode: port mode type. Should be trunk or access
        """
        try:

            action_result = self._remove_vlan_flow(
                vlan_range=vlan_id, port_name=full_name, port_mode=port_mode
            )
            self.result[current_thread().name].append((True, action_result))
        except Exception as e:
            self._logger.error(traceback.format_exc())
            self.result[current_thread().name].append((False, str(e)))
