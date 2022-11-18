from __future__ import annotations


def get_val_from_list_attrs(list_attrs: list[dict[str, str]], name: str) -> str:
    for attr_dict in list_attrs:
        if attr_dict["attributeName"] == name:
            return attr_dict["attributeValue"]
    raise KeyError(f"Attribute '{name}' not found in list of attributes")


def set_val_to_list_attrs(
    list_attrs: list[dict[str, str]], name: str, value: str
) -> None:
    for attr_dict in list_attrs:
        if attr_dict["attributeName"] == name:
            attr_dict["attributeValue"] = value
            break
    else:
        raise KeyError(f"Attribute '{name}' not found in list of attributes")
