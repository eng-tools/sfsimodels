from collections import OrderedDict
import numpy as np

#
# def convert_stress_to_mass(q, width, length, gravity):
#     """
#     Converts a foundation stress to an equivalent mass.
#
#     :param q: applied stress [Pa]
#     :param width: foundation width [m]
#     :param length: foundation length [m]
#     :param gravity: applied gravitational acceleration [m/s2]
#     :return:
#     """
#     mass = q * width * length / gravity
#     return mass


def clean_float(value):
    """Converts a value to a float or returns None"""
    if value is None or value == "":
        return None
    return float(value)


def collect_serial_value(value, export_none=False):
    """
    Introspective function that returns a serialisable value

    The function converts objects to dictionaries
    """
    if isinstance(value, str):
        return value
    elif isinstance(value, int):
        return value
    elif isinstance(value, np.int64):
        return int(value)
    elif hasattr(value, "to_dict"):
        return value.to_dict(export_none=export_none)
    elif hasattr(value, "__len__"):
        tolist = getattr(value, "tolist", None)
        if callable(tolist):
            value = value.tolist()
            return value
        else:
            if hasattr(value, "to_dict"):
                value = value.to_dict(export_none=export_none)
                return value
            else:
                values = []
                for item in value:
                    values.append(collect_serial_value(item, export_none=export_none))
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

    Parameters
    ----------
    obj: object
        An object that parameters should be added to
    dictionary: dict
        Keys are object parameter names, values are object parameter values
    exceptions: list
        Parameters that should be excluded
    verbose: bool
        If true then show print statements
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
                if hasattr(obj, f'set_{key}'):
                    try:
                        getattr(obj, f'set_{key}')(value, two_way=False)
                    except AttributeError:
                        raise AttributeError("Can't set {0}={1} on object: {2}".format(key, value, obj))
                else:
                    raise AttributeError("Can't set {0}={1} on object: {2}".format(key, value, obj))


def get_value_of_a_get_method(obj, method, extras=None):
    """
    Can access exposed 'get' methods and pass in keyword arguments if required

    Parameters
    ----------
    obj: object
        The Object that has the get method
    method: str
        The name of the get method
    extras: dict
        A Dictionary of possible required keyword arguments

    Returns
    -------

    """
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


def interp_left(x0, x, y=None, low=None):
    """
    Interpolation takes the lower value

    Parameters
    ----------
    x0: array_like
        Values to be interpolated on x-axis
    x: array_like
        Existing values on x-axis
    y: array_like
        Existing y-axis values
    low: str or float or int
        What to do if x0 is less than x[0], if ='min' then clip x0 to x[0],
        if float or int then clip to this value, else raise error
    Returns
    -------

    """
    if y is None:
        y = np.arange(len(x))
    else:
        y = np.array(y)
    if low is None:
        assert np.min(x0) >= x[0], (np.min(x0), x[0])
    elif low == 'min':
        x0 = np.clip(x0, x[0], None)
    else:
        x0 = np.clip(x0, low, None)
    inds = np.searchsorted(x, x0, side='right') - 1
    return y[inds]
