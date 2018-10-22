import numpy as np
import pytest
from sfsimodels import sensors

from tests.conftest import TEST_DATA_DIR


def test_get_depth_from_sensor_code():
    sensor_ffp = TEST_DATA_DIR + "test-sensor-file.json"
    si = sensors.read_json_sensor_file(sensor_ffp)
    mtype = "ACC"
    sensor_number = 2
    code = sensors.get_sensor_code_by_number(si, mtype, sensor_number)
    assert code == "ACCX-NFF-S-M"
    depth = sensors.get_depth_by_code(si, code)
    assert depth == 0.0

    code = "ACCX-UB2-L2C-M"  # number = 4
    depth = sensors.get_depth_by_code(si, code)
    assert np.isclose(depth, 63.6)


def test_get_sensor_code_by_number():
    sensor_ffp = TEST_DATA_DIR + "test-sensor-file.json"
    si = sensors.read_json_sensor_file(sensor_ffp)
    mtype = "ACC"
    sensor_number = 2
    code = sensors.get_sensor_code_by_number(si, mtype, sensor_number)
    assert code == "ACCX-NFF-S-M"

    mtype = "DISP"
    sensor_number = 4
    code = sensors.get_sensor_code_by_number(si, mtype, sensor_number)
    assert code == "DISPY-UNB2-S-M"


def test_get_sensor_code_by_number_out_of_bounds():
    sensor_ffp = TEST_DATA_DIR + "test-sensor-file.json"
    si = sensors.read_json_sensor_file(sensor_ffp)
    mtype = "ACC"
    sensor_number = 1000
    with pytest.raises(KeyError):
        sensors.get_sensor_code_by_number(si, mtype, sensor_number, quiet=False)
    sensors.get_sensor_code_by_number(si, mtype, sensor_number, quiet=True)


def test_get_all_sensor_codes():
    sensor_ffp = TEST_DATA_DIR + "test-sensor-file.json"
    si = sensors.read_json_sensor_file(sensor_ffp)
    codes = sensors.get_all_sensor_codes(si, "ACCX-*-*-*")
    expected_codes = [
        "ACCX-NFF-L2C-M",
        "ACCX-NFF-S-M",
        "ACCX-UB2-L2C-M",
    ]
    assert len(codes) == 3
    for code in codes:
        assert code in expected_codes

    codes = sensors.get_all_sensor_codes(si, "*-*-L2C-*")
    expected_codes = ['ACCX-NFF-L2C-M',
                      'ACCX-UB2-L2C-M',
                      'DISPY-UNB2-L2C-MF']
    assert len(codes) == 3
    for code in codes:
        assert code in expected_codes


if __name__ == '__main__':
    test_get_all_sensor_codes()