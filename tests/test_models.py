from sfsimodels import models
from tests.checking_tools import isclose


def test_add_layer_to_soil_profile():
    soil_profile = models.SoilProfile()
    soil = models.Soil()
    soil_profile.add_layer(3, soil)
    soil_profile.add_layer(5, soil)
    soil_profile.add_layer(2.5, soil)
    print(soil_profile.layers)
    layer_order = [0, 2.5, 3, 5]
    ind = 0
    for layer in soil_profile.layers:
        assert layer == layer_order[ind]
        ind += 1


def test_vertical_stress_soil_profile():
    soil_profile = models.SoilProfile()
    soil_profile.add_layer(2, models.Soil())
    soil_profile.add_layer(5, models.Soil())
    unit_weights = [15000.0, 20000.0, 15000.0]
    counter = 0
    for depth in soil_profile.layers:
        soil_profile.layers[depth].unit_dry_weight = unit_weights[counter]
        counter += 1

    assert soil_profile.vertical_total_stress(1) == 15000.0
    assert soil_profile.vertical_total_stress(2) == 30000.0
    assert soil_profile.vertical_total_stress(3) == 50000.0
    assert soil_profile.vertical_total_stress(5) == 90000.0
    assert soil_profile.vertical_total_stress(6) == 105000.0

    soil_profile.gwl = 3.0
    assert soil_profile.vertical_effective_stress(2) == 30000.0
    assert soil_profile.vertical_effective_stress(4) == 60200.0


def test_raft_foundation():
    fd = models.RaftFoundation()
    fd.length = 4
    fd.width = 6
    assert fd.area == 24
    fd.density = 3
    fd.height = 0.1
    assert isclose(fd.mass, 7.2, rel_tol=0.0001)
    i_ll = fd.width ** 3 * fd.length / 12
    i_ww = fd.length ** 3 * fd.width / 12
    assert isclose(fd.i_ll, i_ll, rel_tol=0.001)
    assert isclose(fd.i_ww, i_ww, rel_tol=0.001)


def test_pad_foundation():
    fd = models.PadFoundation()
    fd.length = 15
    fd.pad_length = 3
    fd.n_pads_l = 4
    assert fd.pad_position_l(2) == 9.5
    fd.width = 11
    fd.pad_width = 2
    fd.n_pads_w = 4
    assert fd.pad_position_w(1) == 4.0
    assert fd.pad_i_ww == 3. ** 3 * 2 / 12
    assert fd.pad_i_ll == 2. ** 3 * 3 / 12
    assert fd.pad_area == 2 * 3
    assert isclose(fd.i_ww, 1992.0, rel_tol=0.001)
    assert isclose(fd.i_ll, 1112.0, rel_tol=0.001)
    assert fd.area == 4 * 4 * 2 * 3


if __name__ == '__main__':
    test_pad_foundation()
