import pytest

from cloudshell.shell.flows.connectivity.helpers.dict_action_helpers import (
    get_val_from_list_attrs,
    set_val_to_list_attrs,
)


def test_get_val_from_list_attrs():
    list_attrs = [
        {"attributeName": "name1", "attributeValue": "value1"},
        {"attributeName": "name2", "attributeValue": "value2"},
    ]
    assert "value1" == get_val_from_list_attrs(list_attrs, "name1")
    assert "value2" == get_val_from_list_attrs(list_attrs, "name2")
    with pytest.raises(KeyError):
        get_val_from_list_attrs(list_attrs, "name3")


def test_set_val_to_list_attrs():
    list_attrs = [
        {"attributeName": "name1", "attributeValue": "value1"},
        {"attributeName": "name2", "attributeValue": "value2"},
    ]
    set_val_to_list_attrs(list_attrs, "name1", "new_value1")
    set_val_to_list_attrs(list_attrs, "name2", "new_value2")
    assert "new_value1" == get_val_from_list_attrs(list_attrs, "name1")
    assert "new_value2" == get_val_from_list_attrs(list_attrs, "name2")
    with pytest.raises(KeyError):
        set_val_to_list_attrs(list_attrs, "name3", "new_value3")
