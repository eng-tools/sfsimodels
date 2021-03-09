from collections import OrderedDict
import numpy as np
import sfsimodels.exceptions
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
            try:
                value = objs[obj_base_type][int(value)]
            except KeyError:
                raise KeyError(f'Cannot load type: {obj_base_type}, id: {int(value)}')
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
    # exceptions.append('unique_hash')
    for item in dictionary:
        if item == 'unique_hash':
            obj._loaded_unique_hash = dictionary[item]
            continue
        if item in exceptions:
            continue
        if dictionary[item] is not None:
            if verbose:
                print("process: ", item, dictionary[item])
            key, value = get_key_value(dictionary[item], objs, key=item)
            if verbose:
                print("assign: ", key, value)
            if isinstance(value, dict) and len(value) == 2:  # if is a dict to ref another object
                keys = list(value.keys())
                cleaned_keys = [val.replace('_unique_hash', '') for val in keys]
                if cleaned_keys[0] == cleaned_keys[1]:
                    value = value[cleaned_keys[0]]

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
            except sfsimodels.exceptions.ModelError:
                pass


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


def interp2d(x, xf, f):
    """
    Can interpolate a table to get an array of values in 2D

    Parameters
    ----------
    x: array_like
        1d array of values to be interpolated
    xf: array_like
        1d array of values
    f: array_like
        2d array of function values size=(len(xf), n)

    Returns
    -------
    returns size=(len(x), n)
    Examples
    --------
    >>> f = np.array([[0, 0, 0],
    >>>              [0, 1, 4],
    >>>              [2, 6, 2],
    >>>              [10, 10, 10]
    >>>              ])
    >>> xf = np.array([0, 1, 2, 3])

    >>> x = np.array([0.5, 1, 2.2, 2.5])
    >>> f_interp = interp2d(x, xf, f)
    >>> print(f_interp[0][0])
    0.0
    >>> print(f_interp[0][1])
    0.5
    >>> print(f_interp[0][2])
    2.0
    """
    x = np.array(x)
    xf = np.array(xf)
    f = np.array(f)
    ind = np.argmin(np.abs(x[:, np.newaxis] - xf), axis=1)
    x_ind = xf[ind]
    ind0 = np.where(x_ind > x, ind - 1, ind)
    ind1 = np.where(x_ind > x, ind, ind + 1)
    ind0 = np.clip(ind0, 0, None)
    ind1 = np.clip(ind1, None, len(xf) - 1)
    f0 = f[ind0]
    f1 = f[ind1]
    a0 = xf[ind0]
    a1 = xf[ind1]
    denom = (a1 - a0)
    denom_adj = np.clip(denom, 1e-10, None)  # to avoid divide by zero warning
    s0 = np.where(denom > 0, (x - a0) / denom_adj, 1)  # if denom less than 0, then out of bounds
    s1 = 1 - s0
    return s1[:, np.newaxis] * f0 + s0[:, np.newaxis] * f1


def interp3d(x, y, xs, ys_at_xs, f):
    """
    Can interpolate a table to get an array of values in 2D

    Parameters
    ----------
    x: array_like
        1d array of values to be interpolated
    y: array_like
        1d array of values to be interpolated
    xs: array_like
        1d array of x-positions where points are known
    ys_at_xs: list of array_like
        list of 1d arrays of y-positions where points are known, len=len(x)
    f: list of array_like
        list of 1d arrays of function values size=(len(x), (len(ys_at_xs[j]))

    Returns
    -------
    returns size=(len(x), len(y))
    Examples
    --------
    """
    x_ind0 = interp_left(x, xs)
    x_ind1 = np.clip(x_ind0 + 1, None, len(xs) - 1)
    y_ind_x0y0 = interp_left(y, ys_at_xs[x_ind0])
    y_ind_x0y1 = np.clip(y_ind_x0y0 + 1, None, len(ys_at_xs[x_ind0]) - 1)
    y_ind_x1y0 = interp_left(y, ys_at_xs[x_ind1])
    y_ind_x1y1 = np.clip(y_ind_x1y0 + 1, None, len(ys_at_xs[x_ind1]) - 1)

    x0 = xs[x_ind0]
    x1 = xs[x_ind1]
    y0_at_x0 = ys_at_xs[x_ind0][y_ind_x0y0]
    y1_at_x0 = ys_at_xs[x_ind0][y_ind_x0y1]
    y0_at_x1 = ys_at_xs[x_ind1][y_ind_x1y0]
    y1_at_x1 = ys_at_xs[x_ind1][y_ind_x1y1]

    fx0y0 = f[x_ind0][y_ind_x0y0]
    fx0y1 = f[x_ind0][y_ind_x0y1]
    fx1y0 = f[x_ind1][y_ind_x1y0]
    f1y1 = f[x_ind1][y_ind_x1y1]
    x_w = (x - x0) / ((x1 - x0) + 1e-16 * x1)
    y_w_x0 = (y - y0_at_x0) / ((y1_at_x0 - y0_at_x0) + 1e-16 * y1_at_x0)
    y_w_x1 = (y - y0_at_x1) / ((y1_at_x1 - y0_at_x1) + 1e-16 * y1_at_x1)
    fvs = (fx0y0 * (1 - x_w) * (1 - y_w_x0)) + (fx0y1 * (1 - x_w) * y_w_x0) \
           + (fx1y0 * x_w * (1 - y_w_x1)) + (f1y1 * x_w * y_w_x1)

    return fvs

#
# if __name__ == '__main__':
#     xs = np.array([0, 2])
#     ys_at_xs = np.array([[0, 5, 10], [0, 2, 5, 8, 10]])