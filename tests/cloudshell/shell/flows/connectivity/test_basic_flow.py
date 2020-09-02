#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import unittest
from collections import defaultdict

from cloudshell.shell.flows.connectivity.basic_flow import AbstractConnectivityFlow
from cloudshell.shell.flows.connectivity.utils import get_vm_uid

if sys.version_info >= (3, 0):
    from unittest import mock
else:
    import mock


class TestConnectivityRunner(unittest.TestCase):
    def setUp(self):
        self.logger = mock.MagicMock()
        self.cli_handler = mock.MagicMock()

        class ConnectivityFlow(AbstractConnectivityFlow):
            def _add_vlan_flow(self, *args, **kwargs):
                pass

            def _remove_vlan_flow(self, *args, **kwargs):
                pass

            def _remove_all_vlan_flow(self, *args, **kwargs):
                pass

        self.connectivity_flow = ConnectivityFlow(logger=self.logger)

    def test_abstract_methods(self):
        """Check that all abstract methods are implemented.

        Instance can't be instantiated without implementation of all abstract methods
        """
        with self.assertRaisesRegexp(
            TypeError,
            "Can't instantiate abstract class TestedClass with abstract methods "
            "_add_vlan_flow, _remove_all_vlan_flow, _remove_vlan_flow",
        ):

            class TestedClass(AbstractConnectivityFlow):
                pass

            TestedClass(logger=self.logger)

    @mock.patch("cloudshell.shell.flows.connectivity.basic_flow.current_thread")
    def test_add_vlan_executor(self, current_thread):
        """Check that method will execute add_vlan_flow and add it to the result."""
        vlan_id = "some vlan id"
        full_name = "some full name"
        port_mode = "port mode"
        qnq = mock.MagicMock()
        c_tag = mock.MagicMock()
        vm_uid = mock.MagicMock()
        expected_res = defaultdict(list)
        action_result = mock.MagicMock()
        expected_res[current_thread().name] = [(True, action_result)]
        self.connectivity_flow._add_vlan_flow = mock.MagicMock(
            return_value=action_result
        )
        # act
        self.connectivity_flow._add_vlan_executor(
            vlan_id=vlan_id,
            full_name=full_name,
            port_mode=port_mode,
            qnq=qnq,
            c_tag=c_tag,
            vm_uid=vm_uid,
        )
        # verify
        self.connectivity_flow._add_vlan_flow.assert_called_once_with(
            vlan_range=vlan_id,
            port_mode=port_mode,
            full_name=full_name,
            qnq=qnq,
            c_tag=c_tag,
            vm_uid=vm_uid,
        )

        self.assertEqual(self.connectivity_flow.result, expected_res)

    @mock.patch("cloudshell.shell.flows.connectivity.basic_flow.current_thread")
    def test_add_vlan_executor_fails(self, current_thread):
        """Check that method will correctly handle exception.

        It will execute add_vlan_flow and add an error message to the result
        """
        vlan_id = "some vlan id"
        full_name = "some full name"
        port_mode = "port mode"
        qnq = mock.MagicMock()
        c_tag = mock.MagicMock()
        vm_uid = mock.MagicMock()
        expected_res = defaultdict(list)
        error_msg = "some exception message"
        expected_res[current_thread().name] = [(False, error_msg)]
        self.connectivity_flow._add_vlan_flow = mock.MagicMock(
            side_effect=Exception(error_msg)
        )
        # act
        self.connectivity_flow._add_vlan_executor(
            vlan_id=vlan_id,
            full_name=full_name,
            port_mode=port_mode,
            qnq=qnq,
            c_tag=c_tag,
            vm_uid=vm_uid,
        )
        # verify
        self.connectivity_flow._add_vlan_flow.assert_called_once_with(
            vlan_range=vlan_id,
            port_mode=port_mode,
            full_name=full_name,
            qnq=qnq,
            c_tag=c_tag,
            vm_uid=vm_uid,
        )

        self.assertEqual(self.connectivity_flow.result, expected_res)

    @mock.patch("cloudshell.shell.flows.connectivity.basic_flow.current_thread")
    def test_remove_vlan_executor(self, current_thread):
        """Check that method will execute remove_vlan_flow and add it to the result."""
        vlan_id = "some vlan id"
        full_name = "some full name"
        port_mode = "port mode"
        vm_uid = "vm_uid"
        expected_res = defaultdict(list)
        action_result = mock.MagicMock()
        expected_res[current_thread().name] = [(True, action_result)]
        self.connectivity_flow._remove_vlan_flow = mock.MagicMock(
            return_value=action_result
        )
        # act
        self.connectivity_flow._remove_vlan_executor(
            vlan_id=vlan_id, full_name=full_name, port_mode=port_mode, vm_uid=vm_uid
        )
        # verify
        self.connectivity_flow._remove_vlan_flow.assert_called_once_with(
            vlan_range=vlan_id, port_mode=port_mode, full_name=full_name, vm_uid=vm_uid
        )

        self.assertEqual(self.connectivity_flow.result, expected_res)

    @mock.patch("cloudshell.shell.flows.connectivity.basic_flow.current_thread")
    def test_remove_vlan_failed(self, current_thread):
        """Check that method will correctly handle exception.

        It will execute remove_vlan_flow and add an error message to the result
        """
        vlan_id = "some vlan id"
        full_name = "some full name"
        port_mode = "port mode"
        vm_uid = "vm_uid"
        expected_res = defaultdict(list)
        error_msg = "some exception message"
        expected_res[current_thread().name] = [(False, error_msg)]
        self.connectivity_flow._remove_vlan_flow = mock.MagicMock(
            side_effect=Exception(error_msg)
        )
        # act
        self.connectivity_flow._remove_vlan_executor(
            vlan_id=vlan_id, full_name=full_name, port_mode=port_mode, vm_uid=vm_uid
        )
        # verify
        self.connectivity_flow._remove_vlan_flow.assert_called_once_with(
            vlan_range=vlan_id, port_mode=port_mode, full_name=full_name, vm_uid=vm_uid
        )

        self.assertEqual(self.connectivity_flow.result, expected_res)

    def test_apply_connectivity_changes_no_requests(self):
        """Check that method will raise exception if request is None."""
        with self.assertRaisesRegexp(Exception, "Request is None or empty"):
            self.connectivity_flow.apply_connectivity_changes(request=None)

    @mock.patch("cloudshell.shell.flows.connectivity.basic_flow.jsonpickle")
    @mock.patch(
        "cloudshell.shell.flows.connectivity.basic_flow.JsonRequestDeserializer"
    )
    def test_apply_connectivity_changes_no_json_req_holder(
        self, json_request_deserializer_class, jsonpickle
    ):
        """Check that method will raise exception if json request parsing fails."""
        json_request_deserializer_class.return_value = None
        request = mock.MagicMock()

        with self.assertRaisesRegexp(
            Exception, "Deserialized request is None or empty"
        ):
            self.connectivity_flow.apply_connectivity_changes(request=request)

    @mock.patch("cloudshell.shell.flows.connectivity.basic_flow.DriverResponseRoot")
    @mock.patch("cloudshell.shell.flows.connectivity.basic_flow.jsonpickle")
    @mock.patch(
        "cloudshell.shell.flows.connectivity.basic_flow.JsonRequestDeserializer"
    )
    def test_apply_connectivity_changes(
        self, json_request_deserializer_class, jsonpickle, driver_response_root_class
    ):
        """Check that method will return serialized response."""
        driver_response_root = mock.MagicMock()
        driver_response_root_class.return_value = driver_response_root
        json_request_deserializer = mock.MagicMock(
            driverRequest=mock.MagicMock(actions=[])
        )

        json_request_deserializer_class.return_value = json_request_deserializer
        request = mock.MagicMock()
        # act
        result = self.connectivity_flow.apply_connectivity_changes(request=request)
        # verify
        jsonpickle.encode.assert_called_once_with(
            driver_response_root, unpicklable=False
        )
        self.assertEqual(result, str(jsonpickle.encode()))

    @mock.patch("cloudshell.shell.flows.connectivity.basic_flow.Thread")
    @mock.patch(
        "cloudshell.shell.flows.connectivity.basic_flow.ConnectivitySuccessResponse"
    )
    @mock.patch("cloudshell.shell.flows.connectivity.basic_flow.jsonpickle")
    @mock.patch(
        "cloudshell.shell.flows.connectivity.basic_flow.JsonRequestDeserializer"
    )
    @mock.patch(
        "cloudshell.shell.flows.connectivity.basic_flow.VLANHandler.get_vlan_list"
    )
    def test_apply_connectivity_changes_set_vlan_action_success(
        self,
        get_vlan_list,
        json_request_deserializer_class,
        jsonpickle,
        connectivity_success_response_class,
        thread_class,
    ):
        """Check that method will add success response for the set_vlan action."""
        action_id = "some action id"
        vlan_id = "test vlan id"
        qnq = True
        ctag = "ctag value"
        vm_uid = "vm_uid"
        self.connectivity_flow.result[action_id] = [(True, "success action message")]
        get_vlan_list.return_value = [vlan_id]
        action = mock.MagicMock(
            type="setVlan",
            actionId=action_id,
            connectionParams=mock.MagicMock(
                vlanServiceAttributes=[
                    mock.MagicMock(attributeName="QNQ", attributeValue=str(qnq)),
                    mock.MagicMock(attributeName="CTAG", attributeValue=ctag),
                ]
            ),
            customActionAttributes=[
                mock.MagicMock(attributeName="VM_UUID", attributeValue=vm_uid)
            ],
        )

        json_request_deserializer = mock.MagicMock(
            driverRequest=mock.MagicMock(actions=[action])
        )

        json_request_deserializer_class.return_value = json_request_deserializer
        request = mock.MagicMock()

        # act
        clean_up_mock = mock.MagicMock()
        self.connectivity_flow._remove_all_vlan_flow = clean_up_mock
        self.connectivity_flow.apply_connectivity_changes(request=request)

        # verify
        thread_class.assert_any_call(
            target=clean_up_mock, args=(action.actionTarget.fullName, vm_uid)
        )
        thread_class.assert_any_call(
            target=self.connectivity_flow._add_vlan_executor,
            name=action_id,
            args=(
                vlan_id,
                action.actionTarget.fullName,
                action.connectionParams.mode.lower(),
                qnq,
                ctag,
                vm_uid,
            ),
        )

        connectivity_success_response_class.assert_called_once_with(
            action,
            "Add Vlan {} configuration successfully completed".format(
                action.connectionParams.vlanId
            ),
        )

    @mock.patch(
        "cloudshell.shell.flows.connectivity.basic_flow.ConnectivityErrorResponse"
    )
    @mock.patch("cloudshell.shell.flows.connectivity.basic_flow.jsonpickle")
    @mock.patch(
        "cloudshell.shell.flows.connectivity.basic_flow.JsonRequestDeserializer"
    )
    def test_apply_connectivity_changes_set_vlan_action_error(
        self,
        json_request_deserializer_class,
        jsonpickle,
        connectivity_error_response_class,
    ):
        """Check that method will add error response for the failed set_vlan action."""
        action_id = "some action id"
        self.connectivity_flow._add_vlan_flow = mock.MagicMock(
            side_effect=Exception("failed action message")
        )
        action = mock.MagicMock(type="setVlan", actionId=action_id)
        json_request_deserializer = mock.MagicMock(
            driverRequest=mock.MagicMock(actions=[action])
        )

        json_request_deserializer_class.return_value = json_request_deserializer
        request = mock.MagicMock()

        # act
        self.connectivity_flow.apply_connectivity_changes(request=request)

        # verify
        connectivity_error_response_class.assert_called_once_with(
            action,
            "Add Vlan {} configuration failed.\n"
            "Add Vlan configuration details:\n"
            "failed action message".format(action.connectionParams.vlanId),
        )

    @mock.patch("cloudshell.shell.flows.connectivity.basic_flow.Thread")
    @mock.patch(
        "cloudshell.shell.flows.connectivity.basic_flow.ConnectivitySuccessResponse"
    )
    @mock.patch("cloudshell.shell.flows.connectivity.basic_flow.jsonpickle")
    @mock.patch(
        "cloudshell.shell.flows.connectivity.basic_flow.JsonRequestDeserializer"
    )
    @mock.patch(
        "cloudshell.shell.flows.connectivity.basic_flow.VLANHandler.get_vlan_list"
    )
    def test_apply_connectivity_changes_remove_vlan_action_success(
        self,
        get_vlan_list,
        json_request_deserializer_class,
        jsonpickle,
        connectivity_success_response_class,
        thread_class,
    ):
        """Check that method will add success response for the remove_vlan action."""
        action_id = "some action id"
        vlan_id = "test vlan id"
        self.connectivity_flow.result[action_id] = [(True, "success action message")]
        get_vlan_list.return_value = [vlan_id]

        action = mock.MagicMock(type="removeVlan", actionId=action_id)
        vm_uid = get_vm_uid(action)

        json_request_deserializer = mock.MagicMock(
            driverRequest=mock.MagicMock(actions=[action])
        )

        json_request_deserializer_class.return_value = json_request_deserializer
        request = mock.MagicMock()

        # act
        self.connectivity_flow.apply_connectivity_changes(request=request)
        # verify
        thread_class.assert_any_call(
            target=self.connectivity_flow._remove_vlan_executor,
            name=action_id,
            args=(
                vlan_id,
                action.actionTarget.fullName,
                action.connectionParams.mode.lower(),
                vm_uid,
            ),
        )

        connectivity_success_response_class.assert_called_once_with(
            action,
            "Add Vlan {} configuration successfully completed".format(
                action.connectionParams.vlanId
            ),
        )

    @mock.patch("cloudshell.shell.flows.connectivity.basic_flow.Thread")
    @mock.patch(
        "cloudshell.shell.flows.connectivity.basic_flow.ConnectivitySuccessResponse"
    )
    @mock.patch("cloudshell.shell.flows.connectivity.basic_flow.jsonpickle")
    @mock.patch(
        "cloudshell.shell.flows.connectivity.basic_flow.JsonRequestDeserializer"
    )
    @mock.patch(
        "cloudshell.shell.flows.connectivity.basic_flow.VLANHandler.get_vlan_list"
    )
    def test_apply_connectivity_changes_unknown_action(
        self,
        get_vlan_list,
        json_request_deserializer_class,
        jsonpickle,
        connectivity_success_response_class,
        thread_class,
    ):
        """Check that method will skip unknown action."""
        action_id = "some action id"
        vlan_id = "test vlan id"
        self.connectivity_flow.result[action_id] = [(True, "success action message")]
        get_vlan_list.return_value = [vlan_id]

        action = mock.MagicMock(type="UNKNOWN", actionId=action_id)

        json_request_deserializer = mock.MagicMock(
            driverRequest=mock.MagicMock(actions=[action])
        )

        json_request_deserializer_class.return_value = json_request_deserializer
        request = mock.MagicMock()

        # act
        self.connectivity_flow.apply_connectivity_changes(request=request)

        # verify
        connectivity_success_response_class.assert_called_once_with(
            action,
            "Add Vlan {} configuration successfully completed".format(
                action.connectionParams.vlanId
            ),
        )
