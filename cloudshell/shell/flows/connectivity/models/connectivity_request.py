#!/usr/bin/python
# -*- coding: utf-8 -*-


class AttributeNameValue(object):
    def __init__(self, attribute_name="", attribute_value="", type=""):  # noqa,A002
        """Describes an attribute name value.

        :param str attribute_name: Attribute name
        :param str attribute_value: Attribute value
        :param str type: Object type
        """
        self.type = type
        """:type : str"""
        self.attributeName = attribute_name
        """:type : str"""
        self.attributeValue = attribute_value
        """:type : str"""

    @classmethod
    def from_dict(cls, dictionary):
        att = AttributeNameValue()
        att.type = dictionary["type"]
        att.attributeName = dictionary["attributeName"]
        att.attributeValue = dictionary["attributeValue"]
        return att


class ActionTarget:
    def __init__(self, full_name="", full_address=""):
        """Describes a connectivity action target.

        :param str full_name: full resource name
        :param str full_address: full resource address
        """
        self.fullName = full_name
        """:type : str"""
        self.fullAddress = full_address
        """:type : str"""
        self.type = "actionTarget"
        """:type : str"""

    @classmethod
    def from_dict(cls, dictionary):
        return ActionTarget(
            full_name=dictionary["fullName"], full_address=dictionary["fullAddress"]
        )


class ConnectionParams(object):
    def __init__(
        self, type="", vlan_id="", mode="", vlan_service_attributes=None  # noqa,A002
    ):
        """Describes a connection parameters.

        :param str type:
        :param str vlan_id:
        :param str mode:
        :param list[AttributeNameValue] vlan_service_attributes:
        """
        self.type = type
        self.vlanId = vlan_id
        self.mode = mode
        self.vlanServiceAttributes = vlan_service_attributes or []
        self.type = "setVlanParameter"

    @classmethod
    def from_dict(cls, dictionary):
        con_params = ConnectionParams()
        con_params.vlanId = dictionary["vlanId"]
        con_params.type = dictionary["type"]
        con_params.vlanServiceAttributes = [
            AttributeNameValue.from_dict(attr)
            for attr in dictionary["vlanServiceAttributes"]
        ]
        con_params.mode = dictionary["mode"]
        return con_params


class ConnectivityActionRequest(object):
    SET_VLAN = "setVlan"
    REMOVE_VLAN = "removeVlan"

    def __init__(
        self,
        action_id="",
        type="",  # noqa,A002
        action_target=None,
        connection_id="",
        connection_params=None,
        connector_attributes=None,
        custom_action_attributes=None,
    ):
        """Request to perform a connectivity change.

        :param str action_id: An identifier for this action,
                a response with the corresponding ID is requested
        :param str type: The action type setVlan or removeVlan
        :param ActionTarget action_target:
                The target resource to apply the connectivity change to
        :param str connection_id: The Id of the connection being updated,
        :param ConnectionParams connection_params:
                Specific params for the requested connection type
        :param list[AttributeNameValue] connector_attributes:
                Attributes set on the connector
        :param list[AttributeNameValue] custom_action_attributes:
                Additional attributes for this action
        """
        self.actionId = action_id
        self.type = type
        self.actionTarget = action_target
        self.connectionId = connection_id
        self.connectionParams = connection_params
        self.connectorAttributes = connector_attributes
        self.customActionAttributes = custom_action_attributes

    @classmethod
    def from_dict(cls, json):
        request = ConnectivityActionRequest()
        request.actionId = json["actionId"]
        request.type = json["type"]
        request.actionTarget = ActionTarget.from_dict(json["actionTarget"])
        request.connectionId = json["connectionId"]
        request.connectionParams = ConnectionParams.from_dict(json["connectionParams"])

        if "connectorAttributes" in json:
            request.connectorAttributes = [
                AttributeNameValue.from_dict(attr)
                for attr in json["connectorAttributes"]
            ]
        else:
            request.connectorAttributes = []

        if "customActionAttributes" in json:
            request.customActionAttributes = [
                AttributeNameValue.from_dict(attr)
                for attr in json["customActionAttributes"]
            ]
        else:
            request.customActionAttributes = []

        return request
