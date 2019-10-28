import sys
import unittest
from collections import defaultdict

from cloudshell.shell.flows.connectivity.basic_flow import AbstractConnectivityFlow

if sys.version_info >= (3, 0):
    from unittest import mock
else:
    import mock


class TestConnectivityRunner(unittest.TestCase):
    def setUp(self):
        self.logger = mock.MagicMock()
        self.cli_handler = mock.MagicMock()

        class ConnectivityFlow(AbstractConnectivityFlow):
            def _add_vlan_flow(self):
                pass

            def _remove_vlan_flow(self):
                pass

        self.connectivity_flow = ConnectivityFlow(logger=self.logger)

    def test_abstract_methods(self):
        """Check that all abstract methods are implemented.

        Instance can't be instantiated without implementation of all abstract methods
        """
        with self.assertRaisesRegexp(
            TypeError,
            "Can't instantiate abstract class TestedClass with abstract methods "
            "_add_vlan_flow, _remove_vlan_flow",
        ):

            class TestedClass(AbstractConnectivityFlow):
                pass

            TestedClass(logger=self.logger)

    def test_get_vlan_list(self):
        """Check that method will return list of valid VLANs."""
        vlan_str = "10-15,19,21-23"
        # act
        result = self.connectivity_flow._get_vlan_list(vlan_str=vlan_str)
        # verify
        self.assertEqual(set(result), {"21-23", "19", "10-15"})

    def test_get_vlan_list_vlan_range_range_is_not_supported(self):
        """Check that method will return list with VLANs.

        It will create VLANs between the given range and change start/end if needed
        """
        self.connectivity_flow.IS_VLAN_RANGE_SUPPORTED = False
        vlan_str = "12-10"
        # act
        result = self.connectivity_flow._get_vlan_list(vlan_str=vlan_str)
        # verify
        self.assertEqual(set(result), {"10", "11", "12"})

    def test_get_vlan_list_invalid_vlan_number(self):
        """Check that method will raise Exception if VLAN number is not valid."""
        self.connectivity_flow._validate_vlan_number = mock.MagicMock(
            return_value=False
        )
        vlan_str = "5000"
        # act # verify
        with self.assertRaisesRegexp(Exception, "Wrong VLAN number detected 5000"):
            self.connectivity_flow._get_vlan_list(vlan_str=vlan_str)

    def test_get_vlan_list_invalid_vlan_range(self):
        """Check that method will raise Exception if VLAN range is not valid."""
        self.connectivity_flow.IS_VLAN_RANGE_SUPPORTED = True
        self.connectivity_flow._validate_vlan_range = mock.MagicMock(return_value=False)
        vlan_str = "5000-5005"
        # act # verify
        with self.assertRaisesRegexp(Exception, "Wrong VLANs range detected 5000-5005"):
            self.connectivity_flow._get_vlan_list(vlan_str=vlan_str)

    def test_get_vlan_list_invalid_vlan_range_range_is_not_supported(self):
        """Check that method will raise Exception if VLAN range is not valid."""
        self.connectivity_flow.IS_VLAN_RANGE_SUPPORTED = False
        self.connectivity_flow._validate_vlan_number = mock.MagicMock(
            return_value=False
        )
        vlan_str = "5000-5005"
        # act
        with self.assertRaisesRegexp(Exception, "Wrong VLANs range detected 5000-5005"):
            self.connectivity_flow._get_vlan_list(vlan_str=vlan_str)

    @mock.patch("cloudshell.shell.flows.connectivity.basic_flow.current_thread")
    def test_add_vlan_executor(self, current_thread):
        """Check that method will execute add_vlan_flow and add it to the result."""
        vlan_id = "some vlan id"
        full_name = "some full name"
        port_mode = "port mode"
        qnq = mock.MagicMock()
        c_tag = mock.MagicMock()
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
        )
        # verify
        self.connectivity_flow._add_vlan_flow.assert_called_once_with(
            vlan_range=vlan_id,
            port_mode=port_mode,
            port_name=full_name,
            qnq=qnq,
            c_tag=c_tag,
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
        )
        # verify
        self.connectivity_flow._add_vlan_flow.assert_called_once_with(
            vlan_range=vlan_id,
            port_mode=port_mode,
            port_name=full_name,
            qnq=qnq,
            c_tag=c_tag,
        )

        self.assertEqual(self.connectivity_flow.result, expected_res)

    @mock.patch("cloudshell.shell.flows.connectivity.basic_flow.current_thread")
    def test_remove_vlan_executor(self, current_thread):
        """Check that method will execute remove_vlan_flow and add it to the result."""
        vlan_id = "some vlan id"
        full_name = "some full name"
        port_mode = "port mode"
        expected_res = defaultdict(list)
        action_result = mock.MagicMock()
        expected_res[current_thread().name] = [(True, action_result)]
        self.connectivity_flow._remove_vlan_flow = mock.MagicMock(
            return_value=action_result
        )
        # act
        self.connectivity_flow._remove_vlan_executor(
            vlan_id=vlan_id, full_name=full_name, port_mode=port_mode
        )
        # verify
        self.connectivity_flow._remove_vlan_flow.assert_called_once_with(
            vlan_range=vlan_id, port_mode=port_mode, port_name=full_name
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
        expected_res = defaultdict(list)
        error_msg = "some exception message"
        expected_res[current_thread().name] = [(False, error_msg)]
        self.connectivity_flow._remove_vlan_flow = mock.MagicMock(
            side_effect=Exception(error_msg)
        )
        # act
        self.connectivity_flow._remove_vlan_executor(
            vlan_id=vlan_id, full_name=full_name, port_mode=port_mode
        )
        # verify
        self.connectivity_flow._remove_vlan_flow.assert_called_once_with(
            vlan_range=vlan_id, port_mode=port_mode, port_name=full_name
        )

        self.assertEqual(self.connectivity_flow.result, expected_res)

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

            self.connectivity_flow._validate_request_action(action=Action())

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

            self.connectivity_flow._validate_request_action(action=Action())

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

            self.connectivity_flow._validate_request_action(action=Action())

    def test_apply_connectivity_changes_no_requests(self):
        """Check that method will raise exception if request is None."""
        with self.assertRaisesRegexp(Exception, "request is None or empty"):
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
    def test_apply_connectivity_changes_set_vlan_action_success(
        self,
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
        self.connectivity_flow.result[action_id] = [(True, "success action message")]
        self.connectivity_flow._get_vlan_list = mock.MagicMock(return_value=[vlan_id])
        action = mock.MagicMock(
            type="setVlan",
            actionId=action_id,
            connectionParams=mock.MagicMock(
                vlanServiceAttributes=[
                    mock.MagicMock(attributeName="QNQ", attributeValue=str(qnq)),
                    mock.MagicMock(attributeName="CTAG", attributeValue=ctag),
                ]
            ),
        )

        json_request_deserializer = mock.MagicMock(
            driverRequest=mock.MagicMock(actions=[action])
        )

        json_request_deserializer_class.return_value = json_request_deserializer
        request = mock.MagicMock()

        # act
        self.connectivity_flow.apply_connectivity_changes(request=request)

        # verify
        thread_class.assert_any_call(
            target=self.connectivity_flow._add_vlan_executor,
            name=action_id,
            args=(
                vlan_id,
                action.actionTarget.fullName,
                action.connectionParams.mode.lower(),
                qnq,
                ctag,
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
        self.connectivity_flow.result[action_id] = [(False, "failed action message")]
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
    def test_apply_connectivity_changes_remove_vlan_action_success(
        self,
        json_request_deserializer_class,
        jsonpickle,
        connectivity_success_response_class,
        thread_class,
    ):
        """Check that method will add success response for the remove_vlan action."""
        action_id = "some action id"
        vlan_id = "test vlan id"
        self.connectivity_flow.result[action_id] = [(True, "success action message")]
        self.connectivity_flow._get_vlan_list = mock.MagicMock(return_value=[vlan_id])

        action = mock.MagicMock(type="removeVlan", actionId=action_id)

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
    def test_apply_connectivity_changes_unknown_action(
        self,
        json_request_deserializer_class,
        jsonpickle,
        connectivity_success_response_class,
        thread_class,
    ):
        """Check that method will skip unknown action."""
        action_id = "some action id"
        vlan_id = "test vlan id"
        self.connectivity_flow.result[action_id] = [(True, "success action message")]
        self.connectivity_flow._get_vlan_list = mock.MagicMock(return_value=[vlan_id])

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
