from collections import OrderedDict
import numpy as np

def convert_stress_to_mass(q, width, length, gravity):
    """
    Converts a foundation stress to an equivalent mass.

    :param q: applied stress [Pa]
    :param width: foundation width [m]
    :param length: foundation length [m]
    :param gravity: applied gravitational acceleration [m/s2]
    :return:
    """
    mass = q * width * length / gravity
    return mass


def clean_float(value):
    if value is None or value == "":
        return None
    return float(value)


def collect_serial_value(value):
    if isinstance(value, str):
        return value
    elif isinstance(value, int):
        return value
    elif isinstance(value, np.int64):
        return int(value)
    elif hasattr(value, "to_dict"):
        return value.to_dict()
    elif hasattr(value, "__len__"):
        tolist = getattr(value, "tolist", None)
        if callable(tolist):
            value = value.tolist()
            return value
        else:
            if hasattr(value, "to_dict"):
                value = value.to_dict()
                return value
            else:
                values = []
                for item in value:
                    values.append(collect_serial_value(item))
                return values
    else:
        return value


def get_key_value(value, objs, key=None):
    if key is not None and "_id" == key[-3:]:
        obj_base_type = key[:-3]
        if value is not None:
            value = objs[obj_base_type][int(value)]
        return obj_base_type, value
    elif isinstance(value, list):
        vals = []
        for item in value:
            ikey, val = get_key_value(item, objs)
            vals.append(val)
            # if isinstance(item, list) or isinstance(item, dict) or isinstance(item, OrderedDict):
        return key, vals
    elif isinstance(value, dict):
        vals = {}
        for item in value:
            ikey, ivalue = get_key_value(value[item], objs, key=item)
            vals[ikey] = ivalue
        return key, vals
    elif isinstance(value, OrderedDict):
        vals = OrderedDict()
        for item in value:
            ikey, ivalue = get_key_value(value[item], objs, key=item)
            vals[ikey] = ivalue
        return key, vals
    else:
        return key, value


def add_to_obj(obj, dictionary, objs=None, exceptions=None, verbose=0):
    """
    Cycles through a dictionary and adds the key-value pairs to an object.

    :param obj:
    :param dictionary:
    :param exceptions:
    :param verbose:
    :return:
    """
    if exceptions is None:
        exceptions = []
    exceptions.append('unique_hash')
    for item in dictionary:
        if item in exceptions:
            continue
        if dictionary[item] is not None:
            if verbose:
                print("process: ", item, dictionary[item])
            key, value = get_key_value(dictionary[item], objs, key=item)
            if verbose:
                print("assign: ", key, value)
            try:
                setattr(obj, key, value)
            except AttributeError:
                raise AttributeError("Can't set {0}={1} on object: {2}".format(key, value, obj))


def get_value_of_a_get_method(obj, method, extras=None):
    if extras is None:
        extras = {}
    try:
        value = getattr(obj, method)()
    except TypeError as e:
        if "required positional argument:" in str(e):
            parameters = [str(e).split("argument: ")[-1]]
        elif "required positional arguments:" in str(e):
            p_str = str(e).split("arguments: ")[-1]
            if ", and " in p_str:  # if more than 2
                partial = p_str.split(", and ")
                parameters = partial[0].split(", ") + partial[-1:]
            else:  # if one
                parameters = p_str.split(" and ")
        else:
            raise TypeError(e)
        params = []
        for parameter in parameters:
            parameter = parameter[1:-1]
            if parameter in extras:
                params.append(extras[parameter])
            else:
                params.append(getattr(obj, parameter))

        value = getattr(obj, method)(*params)
    return value

