__author__ = 'maximmillen'


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