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