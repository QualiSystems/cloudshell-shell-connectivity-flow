class JsonRequestDeserializer(object):
    def __init__(self, json):
        for key, value in json.items():
            if isinstance(value, dict):
                setattr(self, key, JsonRequestDeserializer(value))
            elif isinstance(value, list):
                items = [self._create_obj_by_type(item) for item in value]
                setattr(self, key, items)
            else:
                setattr(self, key, self._create_obj_by_type(value))

    @staticmethod
    def _create_obj_by_type(obj):
        obj_type = type(obj)
        if obj_type == dict:
            return JsonRequestDeserializer(obj)
        if obj_type == list:
            return [JsonRequestDeserializer._create_obj_by_type(item) for item in obj]
        if JsonRequestDeserializer._is_primitive(obj):
            return obj_type(obj)
        return obj

    @staticmethod
    def _is_primitive(thing):
        primitive = (int, (type(""), type(u"")), bool, float)
        return isinstance(thing, primitive)


def _list_attrs_to_dict(list_attrs):
    return {attr.attributeName: attr.attributeValue for attr in list_attrs}


def get_vm_uid(action):
    return _list_attrs_to_dict(action.customActionAttributes).get("VM_UUID", "")
