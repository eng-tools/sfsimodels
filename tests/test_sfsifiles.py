import os
from collections import OrderedDict

from tests import load_test_data as ltd
from sfsimodels import files
from sfsimodels import checking_tools as ct
import numpy as np
from sfsimodels import models
import sfsimodels as sm
import json

test_dir = os.path.dirname(__file__)


def test_load_json():
    fp = test_dir + "/test_data/ecp_models.json"
    objs = files.load_json(fp, verbose=0)
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


def test_save_and_load_soil():
    # Set the void ratio and specific gravity
    sl = sm.Soil()
    sl.id = 1
    sl.e_curr = 0.7
    assert sl.unit_dry_weight is None
    sl.specific_gravity = 2.95
    assert np.isclose(sl.unit_dry_weight, 17000, rtol=0.01)

    # set modulus parameters
    g_mod_set = 40e6
    sl.g_mod = g_mod_set
    sl.poissons_ratio = 0.4
    ecp_output = sm.Output()
    ecp_output.add_to_dict(sl)

    ecp_output.name = "a single soil"
    ecp_output.units = "N, kg, m, s"
    ecp_output.comments = ""
    p_str = json.dumps(ecp_output.to_dict(), skipkeys=["__repr__"], indent=4)
    a = open("temp.json", "w")
    a.write(p_str)
    a.close()
    objs = sm.loads_json(p_str, verbose=0)
    loaded_soil = objs['soils'][1]
    assert np.isclose(loaded_soil.g_mod, sl.g_mod)


def test_save_and_load_soil_profile():
    sl1 = models.Soil()
    sl1_gmod = 30e6
    sl1_unit_dry_weight = 16000
    sl1.g_mod = sl1_gmod
    sl1.unit_dry_weight = sl1_unit_dry_weight
    sl2 = models.Soil()
    sl2_cohesion = 20e3
    sl2.cohesion = sl2_cohesion
    sp = models.SoilProfile()
    sp.id = 0
    sp.add_layer(0, sl1)
    sp.add_layer(3, sl2)
    sp.set_soil_ids_to_layers()
    ecp_output = sm.Output()
    ecp_output.add_to_dict(sp)

    ecp_output.name = "a single soil"
    ecp_output.units = "N, kg, m, s"
    ecp_output.comments = ""
    p_str = json.dumps(ecp_output.to_dict(), skipkeys=["__repr__"], indent=4)
    a = open("temp.json", "w")
    a.write(p_str)
    a.close()
    objs = sm.loads_json(p_str, verbose=0)
    loaded_soil = objs['soils'][1]
    load_soil_from_profile = sp.layer(1)
    assert np.isclose(loaded_soil.g_mod, sl1.g_mod)
    assert np.isclose(load_soil_from_profile.g_mod, sl1.g_mod)


def test_save_and_load_building():
    number_of_storeys = 6
    interstorey_height = 3.4  # m
    masses = 40.0e3  # kg
    n_bays = 3

    fb = models.FrameBuilding(number_of_storeys, n_bays)
    fb.id = 1
    fb.interstorey_heights = interstorey_height * np.ones(number_of_storeys)
    fb.floor_length = 18.0  # m
    fb.floor_width = 16.0  # m
    fb.storey_masses = masses * np.ones(number_of_storeys)  # kg

    fb.bay_lengths = [6., 6.0, 6.0]
    fb.set_beam_prop("depth", [0.5, 0.5, 0.5], repeat="up")
    fb.set_beam_prop("width", [0.4, 0.4, 0.4], repeat="up")
    fb.set_column_prop("width", [0.5, 0.5, 0.5, 0.5], repeat="up")
    fb.set_column_prop("depth", [0.5, 0.5, 0.5, 0.5], repeat="up")
    fb.n_seismic_frames = 3
    fb.n_gravity_frames = 0

    ecp_output = sm.Output()
    ecp_output.add_to_dict(fb)

    ecp_output.name = "a single soil"
    ecp_output.units = "N, kg, m, s"
    ecp_output.comments = ""
    p_d = ecp_output.to_dict()
    p_str = json.dumps(ecp_output.to_dict(), skipkeys=["__repr__"], indent=4)
    a = open("temp.json", "w")
    a.write(p_str)
    a.close()


def test_save_and_load_2d_frame_building():
    number_of_storeys = 6
    interstorey_height = 3.4  # m
    masses = 40.0e3  # kg
    n_bays = 3

    fb2d = models.FrameBuilding2D(number_of_storeys, n_bays)
    print(fb2d.inputs)
    fb2d.id = 1
    fb2d.interstorey_heights = interstorey_height * np.ones(number_of_storeys)
    fb2d.floor_length = 18.0  # m
    fb2d.floor_width = 16.0  # m
    fb2d.storey_masses = masses * np.ones(number_of_storeys)  # kg

    fb2d.bay_lengths = [6., 6.0, 6.0]
    fb2d.set_beam_prop("depth", [0.5, 0.5, 0.5], repeat="up")
    fb2d.set_beam_prop("width", [0.4, 0.4, 0.4], repeat="up")
    fb2d.set_column_prop("width", [0.5, 0.5, 0.5, 0.5], repeat="up")
    fb2d.set_column_prop("depth", [0.5, 0.5, 0.5, 0.5], repeat="up")

    ecp_output = sm.Output()
    ecp_output.add_to_dict(fb2d)

    ecp_output.name = "a single building"
    ecp_output.units = "N, kg, m, s"
    ecp_output.comments = ""
    p_d = ecp_output.to_dict()
    p_str = json.dumps(ecp_output.to_dict(), skipkeys=["__repr__"], indent=4)
    a = open("temp.json", "w")
    a.write(p_str)
    a.close()

    # p_str = json.dumps(ecp_output.to_dict(), skipkeys=["__repr__"], indent=4)


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


def test_saturation_set_in_soil_profile():
    sl = models.Soil()
    sl.id = 1
    sl.relative_density = .40  # [decimal]
    sl.unit_dry_weight = 17000  # [N/m3]

    sp = models.SoilProfile()
    sp.hydrostatic = True
    sp.gwl = 4.0
    sp.add_layer(0, sl)
    sp.add_layer(6, sl.deepcopy())
    assert np.isclose(sp.layer(1).saturation, 0.00)
    assert np.isclose(sp.layer(2).saturation, 1.00)

    # Add a layer in between
    sl = models.Soil()
    sl.id = 2
    sl.relative_density = .50  # [decimal]
    sl.unit_dry_weight = 18000  # [N/m3]
    sp.add_layer(2, sl)
    assert np.isclose(sp.layer(2).saturation, 0.50)


def test_can_load_then_save_and_load_custom_ecp_w_custom_obj():
    class Cantilever(object):
        id = None
        type = "cantilever"
        inputs = ["id", "length", "depth", "e_mod"]

        def to_dict(self):
            outputs = OrderedDict()
            for item in self.inputs:
                outputs[item] = getattr(self, item)
            return outputs

    fp = test_dir + "/test_data/ecp_models_w_custom_obj.json"
    objs, meta_data = files.load_json(fp, custom={"cantilever": Cantilever}, meta=True, verbose=0)
    assert ct.isclose(objs["foundations"][1].length, 1.0)
    assert ct.isclose(objs["cantilever"][1].length, 6.0)
    ecp_output = files.Output()
    for m_type in objs:
        for instance in objs[m_type]:
            ecp_output.add_to_dict(objs[m_type][instance])
    ecp_output.name = meta_data["name"]
    ecp_output.units = meta_data["units"]
    ecp_output.comments = meta_data["comments"]
    ecp_output.sfsimodels_version = meta_data["sfsimodels_version"]
    p_str = json.dumps(ecp_output.to_dict(), skipkeys=["__repr__"], indent=4)
    a = open("temp.json", "w")
    a.write(p_str)
    a.close()
    objs2, md2 = files.loads_json(p_str, custom={"cantilever": Cantilever}, meta=True, verbose=0)
    for m_type in objs:
        for instance in objs[m_type]:
            for parameter in objs[m_type][instance].inputs:
                p_org = getattr(objs[m_type][int(instance)], parameter)
                p_2nd = getattr(objs2[m_type][int(instance)], parameter)
                assert p_org == p_2nd, (parameter, p_org, p_2nd)
    for item in meta_data:
        assert meta_data[item] == md2[item], (item, meta_data[item], md2[item])


if __name__ == '__main__':
    # test_load_json()
    # test_full_save_and_load()
    # test_save_and_load_soil_profile()
    test_save_and_load_2d_frame_building()
    # test_full_save_and_load()
    # test_can_load_then_save_and_load_custom_ecp_w_custom_obj()
