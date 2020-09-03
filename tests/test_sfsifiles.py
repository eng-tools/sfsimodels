import os
from collections import OrderedDict

import sfsimodels.models.sections
from tests import load_test_data as ltd
from sfsimodels import files
import numpy as np
from sfsimodels import models
import sfsimodels as sm
import json

test_dir = os.path.dirname(__file__)


def test_load_json():
    fp = test_dir + "/unit_test_data/ecp_models.json"
    objs = files.load_json(fp, verbose=0)
    assert np.isclose(objs["soils"][1].unit_dry_weight, 15564.70588)
    assert np.isclose(objs["foundations"][1].length, 1.0)
    assert np.isclose(objs["soil_profiles"][1].layers[0].unit_dry_weight, 15564.70588)
    rel_density = objs["soil_profiles"][1].layer(2).relative_density
    assert np.isclose(objs["soil_profiles"][1].layer(2).relative_density, 0.7299999994277497), rel_density


def test_load_and_save_structure():
    structure = models.SDOFBuilding()
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
    assert np.isclose(structure.mass_eff, objs['building'][1].mass_eff)


def test_load_and_save_foundation_w_pads():
    fd = models.PadFoundation()
    fd.width = 12  # m
    fd.length = 14  # m
    fd.depth = 0.6  # m
    fd.height = 1.0  # m
    fd.mass = 0.0  # kg
    fd.pad.length = 1.1
    fd.pad.width = 1.1
    fd.n_pads_l = 3
    fd.n_pads_w = 3
    fd.set_pad_pos_in_length_dir_as_equally_spaced()
    fd.set_pad_pos_in_width_dir_as_equally_spaced()
    tie_beams_sect = sm.sections.RCBeamSection()
    tie_beams_sect.depth = fd.height
    tie_beams_sect.width = fd.height
    tie_beams_sect.rc_mat = sm.materials.ReinforcedConcreteMaterial()
    tie_beams_sect.cracked_ratio = 0.6
    fd.tie_beam_sect_in_width_dir = tie_beams_sect
    fd.tie_beam_sect_in_length_dir = tie_beams_sect

    ecp_output = files.Output()
    ecp_output.add_to_dict(fd)
    ecp_output.name = "test data"
    ecp_output.units = "N, kg, m, s"
    ecp_output.comments = ""
    p_str = json.dumps(ecp_output.to_dict(), skipkeys=["__repr__"], indent=4)
    objs = files.loads_json(p_str)
    fd_new = objs['foundation'][1]
    fd_pms = ['width', 'length', 'depth', 'height', 'n_pads_l', 'n_pads_w']
    for item in fd_pms:
        np.isclose(getattr(fd, item), getattr(fd_new, item))
    assert np.sum(abs(fd.pad_pos_in_length_dir - fd_new.pad_pos_in_length_dir)) < 1.0e-6
    assert np.sum(abs(fd.pad_pos_in_width_dir - fd_new.pad_pos_in_width_dir)) < 1.0e-6
    pad_pms = ['width', 'length', 'depth', 'height']
    for item in pad_pms:
        np.isclose(getattr(fd.pad, item), getattr(fd_new.pad, item))


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
    ecp_output_verby = sm.Output()
    ecp_output_verby.add_to_dict(sp, export_none=True)
    p_str = json.dumps(ecp_output_verby.to_dict(), skipkeys=["__repr__"], indent=4)
    assert 'e_min' in p_str
    ecp_output = sm.Output()
    ecp_output.add_to_dict(sp, export_none=False)

    ecp_output.name = "a single soil"
    ecp_output.units = "N, kg, m, s"
    ecp_output.comments = ""
    p_str = json.dumps(ecp_output.to_dict(), skipkeys=["__repr__"], indent=4)
    assert 'e_min' not in p_str
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
    mods = sm.loads_json(p_str)
    bd2 = mods['building'][1]
    print(bd2)
    # a = open("temp.json", "w")
    # a.write(p_str)
    # a.close()


def test_save_and_load_an_element():
    ele = models.buildings.BeamColumnElement()
    ele.sections = [models.sections.RCBeamSection()]
    ele.set_section_prop('width', 0.5)
    ecp_output = sm.Output()
    ecp_output.add_to_dict(ele)
    p_str = json.dumps(ecp_output.to_dict(), skipkeys=["__repr__"], indent=4)
    mods = sm.loads_json(p_str)
    ele2 = mods['beam_column_element'][1]
    s2 = mods['section'][1]
    assert ele2.s[0].width == 0.5, ele2.s[0].width
    assert s2.width == 0.5


def test_save_and_load_wall_building():
    number_of_storeys = 6
    interstorey_height = 3.4  # m
    masses = 40.0e3  # kg
    n_bays = 3

    fb = models.WallBuilding(number_of_storeys)
    fb.id = 1
    fb.interstorey_heights = interstorey_height * np.ones(number_of_storeys)
    fb.floor_length = 18.0  # m
    fb.floor_width = 16.0  # m
    fb.storey_masses = masses * np.ones(number_of_storeys)  # kg

    ecp_output = sm.Output()
    ecp_output.add_to_dict(fb)

    ecp_output.name = "a single wall building"
    ecp_output.units = "N, kg, m, s"
    ecp_output.comments = ""
    p_str = json.dumps(ecp_output.to_dict(), skipkeys=["__repr__"], indent=4)
    objs = sm.loads_json(p_str)
    building = objs["buildings"][1]
    assert np.isclose(building.floor_length, 18.0)
    # a = open("temp.json", "w")
    # a.write(p_str)
    # a.close()


def test_save_and_load_2d_frame_building():
    number_of_storeys = 6
    interstorey_height = 3.4  # m
    masses = 40.0e3  # kg
    n_bays = 3

    fb2d = models.FrameBuilding2D(number_of_storeys, n_bays)
    fb2d.n_storeys = 6
    fb2d.id = 1
    fb2d.interstorey_heights = interstorey_height * np.ones(number_of_storeys)
    fb2d.floor_length = 18.0  # m
    fb2d.floor_width = 16.0  # m
    fb2d.storey_masses = masses * np.ones(number_of_storeys)  # kg

    fb2d.bay_lengths = [6., 6.0, 6.0]
    fb2d.set_beam_prop("depth", [0.5, 0.6, 0.5], repeat="up")
    fb2d.set_beam_prop("width", [0.4, 0.4, 0.4], repeat="up")
    fb2d.set_column_prop("width", [0.5, 0.5, 0.5, 0.5], repeat="up")
    fb2d.set_column_prop("depth", [0.5, 0.5, 0.5, 0.5], repeat="up")
    fb2d.beams[0][0].set_section_prop('a_custom_property', 11)
    fb2d.beams[0][0].add_inputs_to_section(["a_custom_property"])

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

    objs = sm.loads_json(p_str)
    building = objs["buildings"][1]
    assert np.isclose(building.beams[0][0].sections[0].depth, 0.5), building.beams[0][0].sections[0].depth
    assert np.isclose(building.beams[0][1].sections[0].depth, 0.6)

    assert building.beams[0][0].s[0].a_custom_property == 11, building.beams[0][0].sections[0].a_custom_property
    assert np.isclose(building.columns[0][0].sections[0].depth, 0.5)


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
    assert np.isclose(system.bd.mass_eff, objs['buildings'][1].mass_eff)

    soil = system.sp.layer(1)
    for item in soil.inputs:
        if getattr(soil, item) is not None:
            if not isinstance(getattr(soil, item), str):
                assert np.isclose(getattr(soil, item), getattr(objs['soils'][1], item)), item
    for item in system.fd.inputs:
        if getattr(system.fd, item) is not None:
            if isinstance(getattr(system.fd, item), str):
                assert getattr(system.fd, item) == getattr(objs['foundations'][1], item), item
            else:
                assert np.isclose(getattr(system.fd, item), getattr(objs['foundations'][1], item)), item
    for item in system.bd.inputs:
        if getattr(system.bd, item) is not None:
            if isinstance(getattr(system.bd, item), str):
                assert getattr(system.bd, item) == getattr(objs['buildings'][1], item), item
            else:
                assert np.isclose(getattr(system.bd, item), getattr(objs['buildings'][1], item)), item


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
    class Cantilever(sm.CustomObject):
        _id = None
        base_type = "cantilever"
        type = "cantilever"
        inputs = ["id", "length", "depth", "e_mod"]

        def to_dict(self, **kwargs):
            outputs = OrderedDict()
            for item in self.inputs:
                outputs[item] = getattr(self, item)
            return outputs

    fp = test_dir + "/unit_test_data/ecp_models_w_custom_obj.json"
    objs, meta_data = files.load_json_and_meta(fp, custom={"cantilever-cantilever": Cantilever}, verbose=0)
    assert np.isclose(objs["foundation"][1].length, 1.0)
    assert np.isclose(objs["cantilever"][1].length, 6.0)
    ecp_output = files.Output()
    for m_type in objs:
        for instance in objs[m_type]:
            ecp_output.add_to_dict(objs[m_type][instance])
    ecp_output.name = meta_data["name"]
    ecp_output.units = meta_data["units"]
    ecp_output.comments = meta_data["comments"]
    p_str = json.dumps(ecp_output.to_dict(), skipkeys=["__repr__"], indent=4)
    a = open("temp.json", "w")
    a.write(p_str)
    a.close()
    objs2, md2 = files.loads_json(p_str, custom={"cantilever-cantilever": Cantilever}, meta=True, verbose=0)
    for m_type in objs:
        for instance in objs[m_type]:
            for parameter in objs[m_type][instance].inputs:
                p_org = getattr(objs[m_type][int(instance)], parameter)
                p_2nd = getattr(objs2[m_type][int(instance)], parameter)
                assert p_org == p_2nd, (m_type, parameter, p_org, p_2nd)
    for item in meta_data:
        if item == 'sfsimodels_version':
            continue
        assert meta_data[item] == md2[item], (item, meta_data[item], md2[item])


def test_load_frame_w_hinges():
    # Define special class for section
    class CustomBeamSection(sfsimodels.models.sections.Section):
        diametertop = None
        fylong = None
        filongtop = None

        def __init__(self):
            super(CustomBeamSection, self).__init__()
            self._extra_class_variables = [
                "diametertop",
                "fylong",
                "filongtop",
                "myplus_section"
            ]
            self.inputs += self._extra_class_variables

    # Attach the section class as the default for the building
    class CustomBuildingFrame2D(sm.FrameBuilding2D):
        _custom_beam_section = CustomBeamSection
        _custom_column_section = None

    fp = test_dir + "/unit_test_data/building_1011_ecp.json"

    # Override the base_type-type for building-building_frame2D with the custom model
    objs = files.load_json(fp, verbose=0, custom={"building-building_frame2D": CustomBuildingFrame2D})
    bd = objs["building"][1]
    assert np.isclose(bd.floor_length, 13.05)
    assert np.isclose(bd.beams[0][0].s[0].myplus_section, 97.03)
    assert np.isclose(bd.beams[1][1].s[0].myplus_section, 127.85), bd.beams[1][1].s[0].myplus_section
    assert bd.beams[1][0].s[0].diametertop is None
    assert np.isclose(bd.columns[1][0].s[0].nbar_hplusx, 2)
    assert "diametertop" in bd.beams[0][0].s[0].inputs
    ecp_output = files.Output()
    ecp_output.add_to_dict(bd)
    p_str = json.dumps(ecp_output.to_dict(), skipkeys=["__repr__"], indent=4)
    assert '"filongtop"' in p_str
    objs = files.loads_json(p_str)
    bd = objs["building"][1]
    assert np.isclose(bd.beams[0][0].s[0].myplus_section, 97.03)
    assert np.isclose(bd.beams[1][1].s[0].myplus_section, 127.85), bd.beams[1][1].s[0].myplus_section


def test_load_old_file_w_frame_w_hinges():
    # Define special class for section
    class CustomBeamSection(sfsimodels.models.sections.Section):
        diametertop = None
        fylong = None
        filongtop = None

        def __init__(self):
            super(CustomBeamSection, self).__init__()
            self._extra_class_variables = [
                "diametertop",
                "fylong",
                "filongtop",
                "myplus_section"
            ]
            self.inputs += self._extra_class_variables

    # Attach the section class as the default for the building
    class CustomBuildingFrame2D(sm.FrameBuilding2D):
        _custom_beam_section = CustomBeamSection
        _custom_column_section = None

    fp = test_dir + "/unit_test_data/building_1011_ecp_old.json"

    # Override the base_type-type for building-building_frame2D with the custom model
    objs = files.load_json(fp, verbose=0, custom={"building-building_frame2D": CustomBuildingFrame2D})
    bd = objs["building"][1]
    assert np.isclose(bd.floor_length, 13.05)
    assert np.isclose(bd.beams[0][0].s[0].myplus_section, 97.03)
    assert np.isclose(bd.beams[1][1].s[0].myplus_section, 127.85), bd.beams[1][1].s[0].myplus_section
    assert bd.beams[1][0].s[0].diametertop is None
    assert np.isclose(bd.columns[1][0].s[0].nbar_hplusx, 2)
    assert "diametertop" in bd.beams[0][0].s[0].inputs
    ecp_output = files.Output()
    ecp_output.add_to_dict(bd)
    p_str = json.dumps(ecp_output.to_dict(), skipkeys=["__repr__"], indent=4)
    assert '"filongtop"' in p_str
    objs = files.loads_json(p_str)
    bd = objs["building"][1]
    assert np.isclose(bd.beams[0][0].s[0].myplus_section, 97.03)
    assert np.isclose(bd.beams[1][1].s[0].myplus_section, 127.85), bd.beams[1][1].s[0].myplus_section


class Custom3Req(sm.CustomObject):
    type = "custom3"

    def __init__(self, p1, p2, p3):
        super(Custom3Req, self).__init__()

        self._extra_class_variables = ["p1", "p2", "p3"]
        self.inputs += self._extra_class_variables
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3


def test_can_set_more_than_two_positional_args():
    c3 = Custom3Req(1, 3, 5)
    c3.id = 1
    ecp_output = sm.Output()
    ecp_output.add_to_dict(c3)
    p_str = json.dumps(ecp_output.to_dict(), skipkeys=["__repr__"], indent=4)
    objs = sm.loads_json(p_str, custom={"custom_object-custom3": Custom3Req})
    cus = objs["custom_object"][1]
    assert cus.p2 == 3
    assert cus.p3 == 5


def test_save_and_load_soil_w_diff_liq_mass_density():
    sl = models.Soil(liq_mass_density=1.0)
    sl.e_curr = 0.65
    sl.specific_gravity = 2.65
    ecp_output = sm.Output()
    ecp_output.add_to_dict(sl)
    p_str = json.dumps(ecp_output.to_dict(), indent=4)
    print(p_str)
    objs = sm.loads_json(p_str)



if __name__ == '__main__':
    # test_load_json()
    # test_save_and_load_wall_building()
    # test_save_and_load_building()
    # test_load_and_save_structure()
    # test_save_and_load_soil_w_diff_liq_mass_density()
    # test_load_and_save_foundation_w_pads()
    # test_save_and_load_soil_profile()
    # test_save_and_load_an_element()
    # test_save_and_load_building()
    test_save_and_load_2d_frame_building()
    # test_load_json()
    # test_full_save_and_load()
    # test_save_and_load_soil_profile()
    # test_save_and_load_soil()
    # test_can_load_then_save_and_load_custom_ecp_w_custom_obj()
    # test_full_save_and_load()
    # test_can_load_then_save_and_load_custom_ecp_w_custom_obj()
