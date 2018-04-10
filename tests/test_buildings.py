from sfsimodels import models
from sfsimodels.checking_tools import isclose


def test_floor_area():
    building = models.Building()
    building.floor_length = 10.0
    assert building.floor_area is None
    building.floor_width = 12.0
    assert building.floor_area == 120


def test_building_heights():
    building = models.Building()
    building.interstorey_heights = [2, 2, 3]
    assert building.heights[0] == 2
    assert building.heights[1] == 4
    assert building.heights[2] == 7


def test_k_eff():
    structure = models.Structure()
    structure.mass_eff = 10.0
    structure.t_fixed = 1.5
    expected_k_eff = 4.0 * 3.141 ** 2 * 10.0 / 1.5 ** 2
    assert isclose(structure.k_eff, expected_k_eff, rel_tol=0.001)


def test_load_nan():
    bd = models.Building()
    bd.g_mod = ""
    bd.bulk_mod = ""
    bd.g_mod = None
    for item in bd.inputs:
        setattr(bd, item, "")
        setattr(bd, item, None)


if __name__ == '__main__':
    test_load_nan()
    pass
