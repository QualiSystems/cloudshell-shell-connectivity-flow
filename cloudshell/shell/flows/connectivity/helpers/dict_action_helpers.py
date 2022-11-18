from __future__ import annotations

from typing import Any

NOT_SET = object()


def get_val_from_list_attrs(list_attrs: list[dict[str, Any]], name: str) -> Any:
    for attr_dict in list_attrs:
        if attr_dict["attributeName"] == name:
            return attr_dict["attributeValue"]
    raise KeyError(f"Attribute '{name}' not found in list of attributes")


def set_val_to_list_attrs(
    list_attrs: list[dict[str, str]], name: str, value: Any, set_if_eq: Any = NOT_SET
) -> None:
    for attr_dict in list_attrs:
        if attr_dict["attributeName"] == name:
            if set_if_eq is NOT_SET or attr_dict["attributeValue"] == set_if_eq:
                attr_dict["attributeValue"] = value
            break
    else:
        raise KeyError(f"Attribute '{name}' not found in list of attributes")
