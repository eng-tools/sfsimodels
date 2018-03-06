import os

from sfsimodels import files
from sfsimodels import checking_tools as ct
from sfsimodels import models
import json

test_dir = os.path.dirname(__file__)


def test_load_yaml():
    fp = test_dir + "/test_data/_object_load_1.yaml"
    objs = files.load_yaml(fp)
    assert objs["soils"][0].unit_dry_weight == 16400
    assert objs["foundations"][0].length == 7.35
    assert objs["soil_profiles"][0].layers[0].unit_dry_weight == 16400
    assert objs["soil_profiles"][0].layers[0].relative_density == 0.38


def test_load_json():
    fp = test_dir + "/test_data/ecp_models.json"
    objs = files.load_json(fp)
    assert ct.isclose(objs["soils"][1].unit_dry_weight, 15564.70588)
    assert ct.isclose(objs["foundations"][1].length, 1.0)
    assert ct.isclose(objs["soil_profiles"][1].layers[0].unit_dry_weight, 15564.70588)
    rel_density = objs["soil_profiles"][1].layer(1).relative_density
    assert ct.isclose(objs["soil_profiles"][1].layer(1).relative_density, 0.7299999994277497), rel_density


def test_load_and_save_structure():
    structure = models.Structure()
    structure.id = 1
    structure.name = "sample building"
    structure.h_eff = 10.0
    structure.t_fixed = 1.0
    structure.mass_eff = 80000.
    structure.mass_ratio = 1.0  # vertical and horizontal masses are equal
    ecp_output = files.Output()
    ecp_output.add_to_dict(structure)
    ecp_output.name = "test data"
    ecp_output.units = "N, kg, m, s"
    ecp_output.comments = ""

    p_str = json.dumps(ecp_output.to_dict(), skipkeys=["__repr__"], indent=4)
    objs = files.loads_json(p_str)
    assert ct.isclose(structure.mass_eff, objs['buildings'][1].mass_eff)

if __name__ == '__main__':
    test_load_and_save_structure()