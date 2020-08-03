import json


def read_json_sensor_file(ffp):
    """
    Reads the sensor file and stores it as a dictionary.

    :param ffp: full file path to json file
    :return:
    """
    sensor_path = ffp
    si = json.load(open(sensor_path))
    for m_type in si:
        # Convert keys from strings to integers
        si[m_type] = {int(k): v for k, v in si[m_type].items()}
    return si


def get_all_sensor_codes(si, wild_sensor_code):
    """
    Get all sensor sensor_codes that match a wild sensor code

    :param si: dict, sensor index json dictionary
    :param wild_sensor_code: str, a sensor code with "*" for wildcards (e.g. ACCX-*-L2C-*)
    :return:
    """
    mtype_and_ory, x, y, z = wild_sensor_code.split("-")
    if mtype_and_ory == "*":
        mtypes = list(si)
    elif mtype_and_ory[-1] in "XYZ" and "ACCX" not in si:  # Need to support old sensor_file.json files.
        mtypes = [mtype_and_ory[:-1]]
    else:
        mtypes = [mtype_and_ory]

    all_sensor_codes = []
    for mtype in mtypes:
        for m_number in si[mtype]:
            if x in ["*", si[mtype][m_number]['X-CODE']] and \
                    y in ["*", si[mtype][m_number]['Y-CODE']] and \
                    z in ["*", si[mtype][m_number]['Z-CODE']]:
                cc = get_sensor_code_by_number(si, mtype, m_number)
                all_sensor_codes.append(cc)

    return all_sensor_codes


def create_motion_name(test_name, sensor_code, code_suffix=""):
    """
    Builds the full name of the file

    :param test_name: str, test name
    :param sensor_code: str, a sensor code (e.g. ACCX-UB1-L2C-M)
    :param code_suffix: str, suffix
    :return:
    """
    return "%s-%s-%s" % (test_name, sensor_code, code_suffix)


def get_sensor_code_by_number(si, mtype, sensor_number, quiet=False):
    """
    Given a sensor number, get the full sensor code (e.g. ACCX-UB1-L2C-M)

    :param si: dict, sensor index json dictionary
    :param mtype: str, sensor type
    :param sensor_number: int, number of sensor
    :param quiet: bool, if true then return None if not found
    :return: str or None, sensor_code: a sensor code (e.g. ACCX-UB1-L2C-M)
    """
    try:
        if 'Orientation' in si[mtype][sensor_number]:
            orientation = si[mtype][sensor_number]['Orientation']
        else:
            orientation = ""
        return "%s%s-%s-%s-%s" % (mtype,
                                orientation,
                                si[mtype][sensor_number]['X-CODE'],
                                si[mtype][sensor_number]['Y-CODE'],
                                si[mtype][sensor_number]['Z-CODE'])
    except KeyError:
        if quiet:
            return None
        raise


def get_mtype_and_number_from_code(si, sensor_code):
    """
    Given a sensor sensor_code, get motion type and sensor number

    :param si: dict, sensor index json dictionary
    :param sensor_code: str, a sensor code (e.g. ACCX-UB1-L2C-M)
    :return:
    """
    mtype_and_ory, x, y, z = sensor_code.split("-")
    if mtype_and_ory[-1] in "XYZ" and "ACCX" not in si:  # Need to support old sensor_file.json files.
        mtype = mtype_and_ory[:-1]
    else:
        mtype = mtype_and_ory
    for m_number in si[mtype]:
        cc = get_sensor_code_by_number(si, mtype, m_number)
        if cc == sensor_code:
            return mtype, m_number
    return None, None


def get_surface_height(si):
    for mtype in si:
        for m_number in si[mtype]:
            if si[mtype][m_number]["Y-CODE"] == "S":
                return si[mtype][m_number]["y"]
            if si[mtype][m_number]["Y-CODE"] == "0":
                return si[mtype][m_number]["y"]
    return None


def get_depth_by_code(si, sensor_code, coords='auto', surface=None):
    """
    Get depth from surface as a positive value for downwards

    :param si:
    :param sensor_code:
    :param coords:
    :param surface:
    :return:
    """
    mtype, sensor_number = get_mtype_and_number_from_code(si, sensor_code)
    if sensor_number is None:
        raise KeyError("Depth not found for sensor_code: %s" % sensor_code)
    if coords == 'auto':
        surface = get_surface_height(si)
        if surface is None:
            raise ValueError('Cannot detect surface height, define coord system and include surface height as an input')
        return surface - si[mtype][sensor_number]['y']
    elif coords == '+ve':
        return si[mtype][sensor_number]['y']
    elif coords == '-ve':  # FLAC
        return -si[mtype][sensor_number]['y']
    elif coords == 'rev+ve':  # reverse positive (surface is a positive number, numbers decrease with depth)
        if surface is None:
            surface = get_surface_height(si)
        if surface is None:
            raise ValueError('Cannot detect surface height, include surface height as an input')
        return -si[mtype][sensor_number]['y']
    else:
        raise ValueError(f"coords={coords}, does not match: ['auto', '+ve', '-ve', 'rev+ve']")
