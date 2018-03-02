from sfsimodels import models
from sfsimodels.checking_tools import isclose


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


def test_void_ratio_setter():
    sl = models.Soil()
    sl.unit_dry_weight = 17000
    assert sl.specific_gravity is None
    sl.e_curr = 0.7
    assert isclose(sl.specific_gravity, 2.949, rel_tol=0.01)
    # check that unit_dry_weight is still consistent
    sl.unit_dry_weight = 17000


def test_specific_gravity_setter():
    # void ratio then specific gravity
    sl = models.Soil()
    sl.e_curr = 0.7
    assert sl.unit_dry_weight is None
    sl.specific_gravity = 2.95
    assert isclose(sl.unit_dry_weight, 17000, rel_tol=0.01)
    # check that void ratio is still consistent
    sl.e_curr = 0.7

    # specific gravity then void ratio
    sl = models.Soil()
    sl.specific_gravity = 2.95
    assert sl.unit_dry_weight is None
    sl.e_curr = 0.7
    assert isclose(sl.unit_dry_weight, 17000, rel_tol=0.01)
    # check that specific gravity is still consistent
    sl.specific_gravity = 2.95


def test_dry_unit_weight_setter():
    sl = models.Soil()
    sl.e_curr = 0.7
    assert sl.specific_gravity is None
    sl.unit_dry_weight = 17000
    assert isclose(sl.specific_gravity, 2.949, rel_tol=0.01)
    # check that void ratio is still consistent
    sl.e_curr = 0.7


def test_moist_weight_setter():
    sl = models.Soil()
    sl.unit_dry_weight = 17000
    sl.e_curr = 0.7
    assert sl.saturation is None
    sl.unit_moist_weight = 18000
    assert isclose(sl.saturation, 0.248, 0.01)
    print(sl.saturation)


def test_saturation_setter_on_soil():
    sl = models.Soil()
    sl.unit_dry_weight = 17000
    sl.e_curr = 0.7
    assert isclose(sl.unit_sat_weight, 21035.3, rel_tol=0.01)
    assert sl.saturation is None
    assert sl.unit_moist_weight is None
    sl.saturation = 1.0
    assert isclose(sl.unit_moist_weight, 21035.3, rel_tol=0.01)



def test_relative_density_to_e_curr_setter():
    sl = models.Soil()
    sl.e_max = 1.0
    sl.e_min = 0.4
    assert sl.e_curr is None
    sl.relative_density = 0.4
    # expected_void_ratio = sl.e_max - sl.relative_density * (sl.e_max - sl.e_min)
    expected_void_ratio = 0.76
    assert isclose(sl.e_curr, expected_void_ratio, rel_tol=0.01), sl.e_curr
    # reverse
    sl = models.Soil()
    sl.e_max = 1.0
    sl.e_min = 0.4
    assert sl.relative_density is None
    sl.e_curr = 0.76
    # expected_void_ratio = sl.e_max - sl.relative_density * (sl.e_max - sl.e_min)
    expected_relative_density = 0.4
    assert isclose(sl.relative_density, expected_relative_density, rel_tol=0.01), sl.e_curr


def test_relative_density_to_e_min_setter():
    sl = models.Soil()
    sl.e_max = 1.0
    sl.e_curr = 0.76
    assert sl.e_min is None
    sl.relative_density = 0.4
    e_min = 0.4
    assert isclose(sl.e_min, e_min, rel_tol=0.01), sl.e_min

    # reverse
    sl = models.Soil()
    sl.e_max = 1.0
    sl.e_curr = 0.76
    assert sl.relative_density is None
    relative_density = 0.4
    sl.e_min = 0.4
    assert isclose(sl.relative_density, relative_density, rel_tol=0.01), sl.relative_density


def test_relative_density_to_e_max_setter():
    sl = models.Soil()
    sl.e_min = 0.4
    sl.e_curr = 0.76
    assert sl.e_max is None
    sl.relative_density = 0.4
    e_max = 1.0
    actual = sl.e_max
    assert isclose(sl.e_max, e_max, rel_tol=0.01), actual

    # reverse
    sl = models.Soil()
    sl.e_min = 0.4
    sl.e_curr = 0.76
    assert sl.relative_density is None
    relative_density = 0.4
    sl.e_max = 1.0
    actual = sl.relative_density
    assert isclose(sl.relative_density, relative_density, rel_tol=0.01), actual


def test_e_max_to_saturated_weight_setter():
    sl = models.Soil()
    sl.e_min = 0.4
    sl.e_max = 1.0
    sl.unit_dry_weight = 16000
    assert sl.unit_sat_weight is None
    sl.e_curr = 0.76
    assert sl.unit_sat_weight is not None
    sl.relative_density = 0.4
    unit_sat_weight = 20231.818

    assert isclose(sl.unit_sat_weight, unit_sat_weight, rel_tol=0.01), sl.unit_sat_weight

def test_e_max_to_moist_weight_setter():
    sl = models.Soil()
    sl.e_min = 0.4
    sl.e_max = 1.0
    sl.unit_dry_weight = 16000
    assert sl.unit_moist_weight is None
    sl.saturation = 1.0
    sl.e_curr = 0.76
    assert sl.unit_moist_weight is not None
    sl.relative_density = 0.4
    unit_sat_weight = 20231.818

    assert isclose(sl.unit_sat_weight, unit_sat_weight, rel_tol=0.01), sl.unit_sat_weight




if __name__ == '__main__':
    test_moist_weight_setter()
    # test_e_max_to_saturated_weight_setter()