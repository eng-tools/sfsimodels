import os
from tests import load_test_data as ltd
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
    objs = files.load_json(fp, verbose=1)
    assert ct.isclose(objs["soils"][1].unit_dry_weight, 15564.70588)
    assert ct.isclose(objs["foundations"][1].length, 1.0)
    assert ct.isclose(objs["soil_profiles"][1].layers[0].unit_dry_weight, 15564.70588)
    rel_density = objs["soil_profiles"][1].layer(2).relative_density
    assert ct.isclose(objs["soil_profiles"][1].layer(2).relative_density, 0.7299999994277497), rel_density


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


def test_full_save_and_load():
    system = models.SoilStructureSystem()
    ltd.load_test_data(system)
    assert system.fd.length == 18.0
    ecp_output = files.Output()
    ecp_output.add_to_dict(system.sp)
    ecp_output.add_to_dict(system.fd)
    ecp_output.add_to_dict(system.bd)
    ecp_output.add_to_dict(system)
    ecp_output.name = "all test data"
    ecp_output.units = "N, kg, m, s"
    ecp_output.comments = ""
    p_str = json.dumps(ecp_output.to_dict(), skipkeys=["__repr__"], indent=4)
    a = open("temp.json", "w")
    a.write(p_str)
    a.close()
    objs = files.loads_json(p_str, verbose=0)
    assert ct.isclose(system.bd.mass_eff, objs['buildings'][1].mass_eff)

    soil = system.sp.layer(1)
    for item in soil.inputs:
        if getattr(soil, item) is not None:
            if not isinstance(getattr(soil, item), str):
                assert ct.isclose(getattr(soil, item), getattr(objs['soils'][1], item)), item
    for item in system.fd.inputs:
        if getattr(system.fd, item) is not None:
            if isinstance(getattr(system.fd, item), str):
                assert getattr(system.fd, item) == getattr(objs['foundations'][1], item), item
            else:
                assert ct.isclose(getattr(system.fd, item), getattr(objs['foundations'][1], item)), item
    for item in system.bd.inputs:
        if getattr(system.bd, item) is not None:
            if isinstance(getattr(system.bd, item), str):
                assert getattr(system.bd, item) == getattr(objs['buildings'][1], item), item
            else:
                assert ct.isclose(getattr(system.bd, item), getattr(objs['buildings'][1], item)), item

if __name__ == '__main__':
    # test_load_json()
    test_full_save_and_load()