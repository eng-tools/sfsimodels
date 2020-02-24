from sfsimodels import models
import numpy as np


def test_floor_area():
    building = models.Building(1)
    building.floor_length = 10.0
    assert building.floor_area is None
    building.floor_width = 12.0
    assert building.floor_area == 120


def test_building_heights():
    building = models.Building(3)
    building.interstorey_heights = [2, 2, 3]
    assert building.heights[0] == 2
    assert building.heights[1] == 4
    assert building.heights[2] == 7


def test_k_eff():
    structure = models.SDOFBuilding()
    structure.mass_eff = 10.0
    structure.t_fixed = 1.5
    expected_k_eff = 4.0 * 3.141 ** 2 * 10.0 / 1.5 ** 2
    assert np.isclose(structure.k_eff, expected_k_eff, rtol=0.001)


def test_load_nan():
    bd = models.Building(1)
    bd.g_mod = ""
    bd.bulk_mod = ""
    bd.g_mod = None
    ignore_list = ["n_storeys", "interstorey_heights", 'foundation_id']
    for item in bd.inputs:

        if item not in ignore_list:
            setattr(bd, item, "")
            setattr(bd, item, None)


def test_load_frame_building_sample_data():
    """
    Sample data for the FrameBuilding object

    :return:
    """
    number_of_storeys = 6
    interstorey_height = 3.4  # m
    masses = 40.0e3  # kg
    n_bays = 3

    fb = models.FrameBuilding(number_of_storeys, n_bays)
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
    return fb


if __name__ == '__main__':
    test_load_nan()
    pass
