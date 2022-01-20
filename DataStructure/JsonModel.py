import json
from enum import Enum

type_list = [int, float, dict, list, type(None), str, tuple, bool]


def to_dict(obj: object) -> dict:
    global type_list
    results = {}
    for variable_name in obj.__dict__.keys():
        value = obj.__dict__[variable_name]
        if hasattr(value, '__call__'):
            continue
        if type(value) in type_list:
            results[variable_name] = obj.__dict__[variable_name]
        elif type(type(value)) == type(Enum):
            results[variable_name] = obj.__dict__[variable_name].value
        else:
            results[variable_name] = to_dict(value)
    return results


def to_object(json_dict: dict, _class: type) -> object:
    global type_list
    results = _class()
    for variable_name in results.__dict__.keys():
        if variable_name not in json_dict.keys():
            continue
        value = results.__dict__[variable_name]
        if type(value).__name__ == "function":
            continue
        if type(value) in type_list or value in type_list:
            setattr(results, variable_name, json_dict[variable_name])
        elif type(Enum) == type(value):
            setattr(results, variable_name,
                    value(json_dict[variable_name]))
        elif type(type(value)) == type(Enum):
            setattr(results, variable_name,
                    type(value)(json_dict[variable_name]))
        else:
            setattr(results,
                    variable_name,
                    to_object(json_dict[variable_name], value if type(value) is type else type(value)))
    return results


def update_object(json_dict: dict, obj: object) -> list:
    """
    更新对象
    更新对象中json_dict中有的值
    :param json_dict:
    :param obj:
    :return:
    """
    global type_list
    base_class_name = obj.__class__.__name__
    list_changed = []
    for variable_name in obj.__dict__.keys():
        if variable_name not in json_dict.keys():
            continue
        name_path = [f"{base_class_name}.{variable_name}"]
        value = obj.__dict__[variable_name]
        _type = value if type(value) is type else type(value)
        if _type in type_list or value in type_list:
            setattr(obj, variable_name, json_dict[variable_name])
        elif _type == type(Enum):
            setattr(obj, variable_name, _type(json_dict[variable_name]))
        elif type(_type) == type(Enum):
            setattr(obj, variable_name, _type(json_dict[variable_name]))
        else:
            name_path += [(f"{base_class_name}.{variable_name}."
                           + result) for result in update_object(json_dict[variable_name], obj.__dict__[variable_name])]
        list_changed += name_path
    return list_changed


class JObject:
    def __init__(self, **kwargs):
        json_object: dict = None
        _type: type = None
        for key, value in kwargs.items():
            if key == "json":
                json_object, _type = (json.loads(value), type(self))

        if json_object is not None and _type is not None:
            obj = to_object(json_object, _type)
            for variable_name in obj.__dict__.keys():
                setattr(self,
                        variable_name,
                        getattr(obj, variable_name))

    def json(self):
        return json.dumps(to_dict(self), sort_keys=True, indent=4, separators=(', ', ': '))

    def __str__(self):
        return self.json()

    def update(self, json_str: str) -> list:
        return update_object(json.loads(json_str), self)


class Example(JObject):
    def __init__(self, **kwargs):
        self.a: int = 1
        self.b: int = int
        self.c: float = 0.0
        self.d: str = ""

        super().__init__(**kwargs)
