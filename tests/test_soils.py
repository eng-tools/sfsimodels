import pytest

from sfsimodels import models
from sfsimodels.checking_tools import isclose
from sfsimodels import exceptions


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
    soil_profile.layer(1).unit_sat_weight = 21000
    assert soil_profile.vertical_effective_stress(2) == 30000.0
    assert soil_profile.vertical_effective_stress(4) == 61200.0


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


def test_bulk_to_g_mod_setter():
    expected_bulk_mod = 1e6
    expected_poissons_ratio = 0.3
    expected_g_mod = 461538.46
    # b - v - g
    sl = models.Soil()
    sl.bulk_mod = expected_bulk_mod
    assert sl.g_mod is None
    sl.poissons_ratio = expected_poissons_ratio
    assert isclose(sl.g_mod, expected_g_mod, rel_tol=0.01), sl.g_mod
    # b - g - v
    sl = models.Soil()
    sl.bulk_mod = expected_bulk_mod
    assert sl.poissons_ratio is None
    sl.g_mod = expected_g_mod
    assert isclose(sl.poissons_ratio, expected_poissons_ratio, rel_tol=0.01), sl.poissons_ratio
    # g - v - b
    sl = models.Soil()
    sl.g_mod = expected_g_mod
    assert sl.bulk_mod is None
    sl.poissons_ratio = expected_poissons_ratio
    assert isclose(sl.bulk_mod, expected_bulk_mod, rel_tol=0.01), sl.bulk_mod
    # g - b - v
    sl = models.Soil()
    sl.g_mod = expected_g_mod
    assert sl.poissons_ratio is None
    sl.bulk_mod = expected_bulk_mod
    assert isclose(sl.poissons_ratio, expected_poissons_ratio, rel_tol=0.01), sl.poissons_ratio
    # v - b - g
    sl = models.Soil()
    sl.poissons_ratio = expected_poissons_ratio
    assert sl.g_mod is None
    sl.bulk_mod = expected_bulk_mod
    assert isclose(sl.g_mod, expected_g_mod, rel_tol=0.01), sl.g_mod
    # v - g - b
    sl = models.Soil()
    sl.poissons_ratio = expected_poissons_ratio
    assert sl.bulk_mod is None
    sl.g_mod = expected_g_mod
    assert isclose(sl.bulk_mod, expected_bulk_mod, rel_tol=0.01), sl.bulk_mod


def test_soil_profile_vertical_total_stress():
    soil_1 = models.Soil()
    soil_1.phi = 33.
    soil_1.cohesion = 50000
    soil_1.unit_dry_weight = 18000
    soil_profile = models.SoilProfile()
    soil_profile.add_layer(0, soil_1)
    assert isclose(soil_profile.vertical_total_stress(5), 5 * 18000, rel_tol=0.0001)
    soil_profile.gwl = 3.
    assert isclose(soil_profile.vertical_total_stress(3), 3 * 18000, rel_tol=0.0001)
    with pytest.raises(exceptions.AnalysisError):
        soil_profile.vertical_effective_stress(4)
    soil_profile.layer(0).unit_sat_weight = 21000
    expected = 3 * 18000 + 2 * 21000
    assert isclose(soil_profile.vertical_total_stress(5), expected, rel_tol=0.0001)
    soil_2 = models.Soil()
    soil_2.phi = 33.
    soil_2.cohesion = 50000
    soil_2.unit_dry_weight = 16000

    # CONSIDER TWO LAYER SOIL PROFILE
    soil_profile.add_layer(4., soil_2)
    soil_profile.gwl = 10000  # Dry first
    assert isclose(soil_profile.vertical_total_stress(5), 4 * 18000 + 1 * 16000, rel_tol=0.0001)
    soil_profile.gwl = 3.
    with pytest.raises(exceptions.AnalysisError):
        soil_profile.vertical_effective_stress(5)
    soil_profile.layer(1).unit_sat_weight = 20000
    expected = 3 * 18000 + 1 * 21000 + 1 * 20000
    assert isclose(soil_profile.vertical_total_stress(5), expected, rel_tol=0.0001)


def test_soil_profile_vertical_effective_stress():
    soil_1 = models.Soil()
    soil_1.phi = 33.
    soil_1.cohesion = 50000
    soil_1.unit_dry_weight = 18000
    soil_2 = models.Soil()
    soil_2.phi = 33.
    soil_2.cohesion = 50000
    soil_2.unit_dry_weight = 18000
    soil_profile = models.SoilProfile()
    soil_profile.add_layer(0, soil_1)
    soil_profile.add_layer(5., soil_2)
    z_c = 5.0
    gwl = 4.0
    soil_profile.gwl = gwl

    assert soil_1.unit_sat_weight is None
    assert isclose(soil_profile.vertical_effective_stress(2), 2 * 18000, rel_tol=0.0001)
    with pytest.raises(exceptions.AnalysisError):
        soil_profile.vertical_effective_stress(z_c)
    soil_1.unit_sat_weight = 21000
    expected_sigma_veff = (z_c - gwl) * (21000 - 9800) + gwl * 18000
    assert isclose(soil_profile.vertical_effective_stress(z_c), expected_sigma_veff, rel_tol=0.0001)


def test_inputs_soil():
    sl = models.Soil()
    assert "g_mod" in sl.inputs
    assert "e_cr0" not in sl.inputs
    crit_sl = models.CriticalSoil()
    assert "g_mod" in crit_sl.inputs
    assert "e_cr0" in crit_sl.inputs


def test_e_critical():
    crit_sl = models.CriticalSoil()
    crit_sl.e_cr0 = 0.79  # Jin et al. 2015
    crit_sl.p_cr0 = 10  # Jin et al. 2015
    crit_sl.lamb_crl = 0.015  # Jin et al. 2015

    assert isclose(crit_sl.e_critical(1.8), 0.81572, rel_tol=0.0001)


def test_load_test_data():
    from tests import load_test_data as ltd
    soil = models.Soil()
    ltd.load_soil_test_data(soil)


def test_load_nan():
    sl = models.Soil()
    sl.g_mod = ""
    sl.bulk_mod = ""
    sl.g_mod = None
    for item in sl.inputs:
        setattr(sl, item, "")
        setattr(sl, item, None)


def test_override():
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
    assert isclose(sl.unit_sat_weight, unit_sat_weight, rel_tol=0.001), sl.unit_sat_weight

    # Can call override when value is consistent
    sl.override("unit_sat_weight", unit_sat_weight)
    # Can call override when value is inconsistent, but it removes some of the stack
    new_unit_sat_weight = 19000.
    conflicts = sl.override("unit_sat_weight", new_unit_sat_weight)
    expected_conflicts = ['e_curr', 'relative_density']
    assert len(conflicts) == len(expected_conflicts)
    for i in range(len(conflicts)):
        assert conflicts[i] == expected_conflicts[i]
    assert isclose(sl.unit_sat_weight, new_unit_sat_weight, rel_tol=0.001), sl.unit_sat_weight


def test_can_override_all():
    from tests import load_test_data as ltd
    soil = models.Soil()
    ltd.load_soil_test_data(soil)
    soil.reset_all()
    for item in soil.inputs:
        soil2 = soil.deepcopy()
        value = getattr(soil, item)
        if value is not None:
            soil2.override(item, value * 1.3)
            assert getattr(soil2, item) == value * 1.3


def test_override_fake_key():
    sl = models.Soil()
    with pytest.raises(KeyError):
        sl.override("not_a_parameter", 1)


def test_reset_all():
    from tests import load_test_data as ltd
    soil = models.Soil()
    ltd.load_soil_test_data(soil)
    soil.reset_all()
    for item in soil.inputs:
        assert getattr(soil, item) is None


if __name__ == '__main__':
    # test_reset_all()
    # test_override_fake_key()
    test_override()
    # test_soil_profile_vertical_effective_stress()
    # test_e_max_to_saturated_weight_setter()