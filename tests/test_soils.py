import pytest
import os

from sfsimodels import files
from sfsimodels import models
import numpy as np
from tests.test_soil_profiles import test_soil_profile_split_complex_stress_dependent


def test_void_ratio_setter():
    sl = models.Soil()
    sl.unit_dry_weight = 17000
    assert sl.specific_gravity is None
    sl.e_curr = 0.7
    assert np.isclose(sl.specific_gravity, 2.949, rtol=0.01)
    # check that unit_dry_weight is still consistent
    sl.unit_dry_weight = 17000


def test_specific_gravity_setter():
    # void ratio then specific gravity
    sl = models.Soil()
    sl.e_curr = 0.7
    assert sl.unit_dry_weight is None
    sl.specific_gravity = 2.95
    assert np.isclose(sl.unit_dry_weight, 17000, rtol=0.01)
    # check that void ratio is still consistent
    sl.e_curr = 0.7

    # specific gravity then void ratio
    sl = models.Soil()
    sl.specific_gravity = 2.95
    assert sl.unit_dry_weight is None
    sl.e_curr = 0.7
    assert np.isclose(sl.unit_dry_weight, 17000, rtol=0.01)
    # check that specific gravity is still consistent
    sl.specific_gravity = 2.95


def test_dry_unit_weight_setter():
    sl = models.Soil()
    sl.e_curr = 0.7
    assert sl.specific_gravity is None
    sl.unit_dry_weight = 17000
    assert np.isclose(sl.specific_gravity, 2.949, rtol=0.01)
    # check that void ratio is still consistent
    sl.e_curr = 0.7


def test_auto_set_unit_sat_weight():
    sl = models.Soil()
    sl.e_curr = 0.7
    assert sl.specific_gravity is None
    sl.unit_dry_weight = 17000
    assert np.isclose(sl.unit_sat_weight, 21035.294, rtol=0.01)


def test_auto_set_unit_dry_weight_from_sat():
    sl = models.Soil()
    sl.e_curr = 0.7
    assert sl.specific_gravity is None
    sl.unit_sat_weight = 21035.294
    assert np.isclose(sl.unit_dry_weight, 17000, rtol=0.01)


def test_auto_e_curr_from_sat():
    sl = models.Soil()
    sl.specific_gravity = 2.7
    sl.unit_sat_weight = 21000.0
    assert np.isclose(sl.e_curr, 0.4875)


def test_moist_weight_setter():
    sl = models.Soil()
    sl.unit_dry_weight = 17000
    sl.e_curr = 0.7
    assert sl.saturation is None
    sl.unit_moist_weight = 18000
    assert np.isclose(sl.saturation, 0.248, 0.01)


def test_saturation_setter_on_soil():
    sl = models.Soil()
    sl.unit_dry_weight = 17000
    sl.e_curr = 0.7
    assert np.isclose(sl.unit_sat_weight, 21035.3, rtol=0.01)
    assert sl.saturation is None
    assert sl.unit_moist_weight is None
    sl.saturation = 1.0
    assert np.isclose(sl.unit_moist_weight, 21035.3, rtol=0.01)


def test_relative_density_to_e_curr_setter():
    sl = models.Soil()
    sl.e_max = 1.0
    sl.e_min = 0.4
    assert sl.e_curr is None
    sl.relative_density = 0.4
    # expected_void_ratio = sl.e_max - sl.relative_density * (sl.e_max - sl.e_min)
    expected_void_ratio = 0.76
    assert np.isclose(sl.e_curr, expected_void_ratio, rtol=0.01), sl.e_curr
    # reverse
    sl = models.Soil()
    sl.e_max = 1.0
    sl.e_min = 0.4
    assert sl.relative_density is None
    sl.e_curr = 0.76
    # expected_void_ratio = sl.e_max - sl.relative_density * (sl.e_max - sl.e_min)
    expected_relative_density = 0.4
    assert np.isclose(sl.relative_density, expected_relative_density, rtol=0.01), sl.e_curr


def test_relative_density_to_e_min_setter():
    sl = models.Soil()
    sl.e_max = 1.0
    sl.e_curr = 0.76
    assert sl.e_min is None
    sl.relative_density = 0.4
    e_min = 0.4
    assert np.isclose(sl.e_min, e_min, rtol=0.01), sl.e_min

    # reverse
    sl = models.Soil()
    sl.e_max = 1.0
    sl.e_curr = 0.76
    assert sl.relative_density is None
    relative_density = 0.4
    sl.e_min = 0.4
    assert np.isclose(sl.relative_density, relative_density, rtol=0.01), sl.relative_density


def test_relative_density_to_e_max_setter():
    sl = models.Soil()
    sl.e_min = 0.4
    sl.e_curr = 0.76
    assert sl.e_max is None
    sl.relative_density = 0.4
    e_max = 1.0
    actual = sl.e_max
    assert np.isclose(sl.e_max, e_max, rtol=0.01), actual

    # reverse
    sl = models.Soil()
    sl.e_min = 0.4
    sl.e_curr = 0.76
    assert sl.relative_density is None
    relative_density = 0.4
    sl.e_max = 1.0
    actual = sl.relative_density
    assert np.isclose(sl.relative_density, relative_density, rtol=0.01), actual


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

    assert np.isclose(sl.unit_sat_weight, unit_sat_weight, rtol=0.01), sl.unit_sat_weight


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

    assert np.isclose(sl.unit_sat_weight, unit_sat_weight, rtol=0.01), sl.unit_sat_weight


def test_bulk_to_g_mod_setter():
    expected_bulk_mod = 1e6
    expected_poissons_ratio = 0.3
    expected_g_mod = 461538.46
    # b - v - g
    sl = models.Soil()
    sl.bulk_mod = expected_bulk_mod
    assert sl.g_mod is None
    sl.poissons_ratio = expected_poissons_ratio
    assert np.isclose(sl.g_mod, expected_g_mod, rtol=0.01), sl.g_mod
    # b - g - v
    sl = models.Soil()
    sl.bulk_mod = expected_bulk_mod
    assert sl.poissons_ratio is None
    sl.g_mod = expected_g_mod
    assert np.isclose(sl.poissons_ratio, expected_poissons_ratio, rtol=0.01), sl.poissons_ratio
    # g - v - b
    sl = models.Soil()
    sl.g_mod = expected_g_mod
    assert sl.bulk_mod is None
    sl.poissons_ratio = expected_poissons_ratio
    assert np.isclose(sl.bulk_mod, expected_bulk_mod, rtol=0.01), sl.bulk_mod
    # g - b - v
    sl = models.Soil()
    sl.g_mod = expected_g_mod
    assert sl.poissons_ratio is None
    sl.bulk_mod = expected_bulk_mod
    assert np.isclose(sl.poissons_ratio, expected_poissons_ratio, rtol=0.01), sl.poissons_ratio
    # v - b - g
    sl = models.Soil()
    sl.poissons_ratio = expected_poissons_ratio
    assert sl.g_mod is None
    sl.bulk_mod = expected_bulk_mod
    assert np.isclose(sl.g_mod, expected_g_mod, rtol=0.01), sl.g_mod
    # v - g - b
    sl = models.Soil()
    sl.poissons_ratio = expected_poissons_ratio
    assert sl.bulk_mod is None
    sl.g_mod = expected_g_mod
    assert np.isclose(sl.bulk_mod, expected_bulk_mod, rtol=0.01), sl.bulk_mod


def test_inputs_soil():
    sl = models.Soil()
    assert "g_mod" in sl.inputs
    assert "e_cr0" not in sl.inputs
    crit_sl = models.CriticalSoil()
    assert "g_mod" in crit_sl.inputs
    assert "e_cr0" in crit_sl.inputs


def test_e_critical():
    crit_sl = models.CriticalSoil(pw=9800)
    crit_sl.e_cr0 = 0.79  # Jin et al. 2015
    crit_sl.p_cr0 = 10  # Jin et al. 2015
    crit_sl.lamb_crl = 0.015  # Jin et al. 2015

    assert np.isclose(crit_sl.e_critical(1.8), 0.81572, rtol=0.0001)


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
    assert np.isclose(sl.unit_sat_weight, unit_sat_weight, rtol=0.001), sl.unit_sat_weight

    # Can call override when value is consistent
    sl.override("unit_sat_weight", unit_sat_weight)
    # Can call override when value is inconsistent, but it removes some of the stack
    new_unit_sat_weight = 19000.
    conflicts = sl.override("unit_sat_weight", new_unit_sat_weight)
    expected_conflicts = ['e_curr', 'relative_density']
    assert len(conflicts) == len(expected_conflicts)
    for i in range(len(conflicts)):
        assert conflicts[i] == expected_conflicts[i]
    assert np.isclose(sl.unit_sat_weight, new_unit_sat_weight, rtol=0.001), sl.unit_sat_weight


def test_can_override_all():
    from tests import load_test_data as ltd
    soil = models.Soil()
    ltd.load_soil_test_data(soil)
    soil.reset_all()
    for item in soil.inputs:
        soil2 = soil.deepcopy()
        value = getattr(soil, item)
        if value is not None and not isinstance(value, str):
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
    exception_list = ["base_type", "type", "stype"]
    for item in soil.inputs:
        if item not in exception_list:
            assert getattr(soil, item) is None


def test_can_compute_layer_depth():
    test_dir = os.path.dirname(__file__)
    fp = test_dir + "/unit_test_data/ecp_models.json"
    objs = files.load_json(fp)
    soil_profile = objs["soil_profiles"][1]
    assert isinstance(soil_profile, models.SoilProfile)

    assert np.isclose(soil_profile.layers[0].unit_dry_weight, 15564.70588)
    rel_density = soil_profile.layer(2).relative_density
    assert np.isclose(rel_density, 0.7299999994277497), rel_density
    assert soil_profile.layer(1).id == 1
    assert soil_profile.get_layer_depth(2) == 4.0
    assert soil_profile.get_layer_height(2) == 4.0
    assert soil_profile.get_layer_mid_depth(2) == 6.0


def test_poissons_ratio_again():
    soil = models.Soil()
    g_mod = 60000000.0
    bulk_mod = 87142857.14285
    poissons_ratio = 0.22
    soil.g_mod = g_mod
    soil.bulk_mod = bulk_mod
    soil.poissons_ratio = poissons_ratio
    soil2 = models.Soil()
    soil2.bulk_mod = bulk_mod
    soil2.g_mod = g_mod
    soil2.poissons_ratio = poissons_ratio


if __name__ == '__main__':
    # test_e_critical()
    test_auto_set_unit_dry_weight_from_sat()
    # test_poissons_ratio_again()
    # test_reset_all()
    # test_override_fake_key()
    # test_can_compute_layer_depth()
    # test_get_layer_index_by_depth()
    # test_get_soil_at_depth_in_soil_profile()
    # test_soil_profile_vertical_effective_stress()
    # test_e_max_to_saturated_weight_setter()