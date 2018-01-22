import os

from sfsimodels import files

test_dir = os.path.dirname(__file__)


def test_load_yaml():
    fp = test_dir + "/test_data/_object_load_1.yaml"
    objs = files.load_yaml(fp)
    assert objs["soils"][0].unit_dry_weight == 16400
    assert objs["foundations"][0].length == 7.35
    assert objs["soil_profiles"][0].layers[0].unit_dry_weight == 16400
    assert objs["soil_profiles"][0].layers[0].relative_density == 0.38