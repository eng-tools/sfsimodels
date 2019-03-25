import pytest
import os

from sfsimodels import files
from sfsimodels import models
import sfsimodels as sm
import numpy as np
from sfsimodels import exceptions


def test_add_layer_to_soil_profile():
    soil_profile = models.SoilProfile()
    soil = models.Soil()
    soil_profile.add_layer(3, soil)
    soil_profile.add_layer(5, soil)
    soil_profile.add_layer(2.5, soil)
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
    soil_profile.layer(2).unit_sat_weight = 21000
    assert soil_profile.vertical_effective_stress(2) == 30000.0
    assert soil_profile.vertical_effective_stress(4) == 61200.0


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


def test_soil_profile_vertical_total_stress():
    soil_1 = models.Soil()
    soil_1.phi = 33.
    soil_1.cohesion = 50000
    soil_1.unit_dry_weight = 18000
    soil_profile = models.SoilProfile()
    soil_profile.add_layer(0, soil_1)
    assert np.isclose(soil_profile.vertical_total_stress(5), 5 * 18000, rtol=0.0001)
    soil_profile.gwl = 3.
    assert np.isclose(soil_profile.vertical_total_stress(3), 3 * 18000, rtol=0.0001)
    with pytest.raises(exceptions.AnalysisError):
        soil_profile.vertical_effective_stress(4)
    soil_profile.layer(1).unit_sat_weight = 21000
    expected = 3 * 18000 + 2 * 21000
    assert np.isclose(soil_profile.vertical_total_stress(5), expected, rtol=0.0001)
    soil_2 = models.Soil()
    soil_2.phi = 33.
    soil_2.cohesion = 50000
    soil_2.unit_dry_weight = 16000

    # CONSIDER TWO LAYER SOIL PROFILE
    soil_profile.add_layer(4., soil_2)
    soil_profile.gwl = 10000  # Dry first
    assert np.isclose(soil_profile.vertical_total_stress(5), 4 * 18000 + 1 * 16000, rtol=0.0001)
    soil_profile.gwl = 3.
    with pytest.raises(exceptions.AnalysisError):
        soil_profile.vertical_effective_stress(5)
    soil_profile.layer(2).unit_sat_weight = 20000
    expected = 3 * 18000 + 1 * 21000 + 1 * 20000
    assert np.isclose(soil_profile.vertical_total_stress(5), expected, rtol=0.0001)


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
    assert np.isclose(soil_profile.vertical_effective_stress(2), 2 * 18000, rtol=0.0001)
    with pytest.raises(exceptions.AnalysisError):
        soil_profile.vertical_effective_stress(z_c)
    soil_1.unit_sat_weight = 21000
    expected_sigma_veff = (z_c - gwl) * (21000 - 9800) + gwl * 18000
    assert np.isclose(soil_profile.vertical_effective_stress(z_c), expected_sigma_veff, rtol=0.0001)


def test_hydrostatic_pressure():
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
    assert np.isclose(soil_profile.hydrostatic_pressure(2), 0.0, rtol=0.0001)
    assert np.isclose(soil_profile.hydrostatic_pressure(z_c), 9800, rtol=0.0001)


def test_stress_dependent_soil_g_mod():
    soil_1 = models.Soil()
    soil_1.phi = 33.
    soil_1.unit_dry_weight = 18000
    soil_1.specific_gravity = 2.65
    soil_2 = sm.StressDependentSoil()
    soil_2.phi = 33.
    soil_2.cohesion = 50000
    soil_2.unit_dry_weight = 18000
    soil_2.g0_mod = 500.
    soil_profile = models.SoilProfile()
    soil_profile.add_layer(0, soil_1)
    soil_profile.add_layer(5., soil_2)
    z_c = 5.0
    gwl = 4.0
    soil_profile.gwl = gwl

    assert np.isclose(soil_1.unit_sat_weight, 21007.5471698, rtol=0.0001)
    assert np.isclose(soil_profile.hydrostatic_pressure(z_c), 9800, rtol=0.0001)
    v_eff = soil_profile.vertical_effective_stress(z_c)
    assert np.isclose(soil_2.g_mod_at_v_eff_stress(v_eff), 36580544.6888, rtol=0.0001)
    m_eff = v_eff * (1 + 2 * (1 - np.sin(soil_2.phi_r))) / 3
    assert np.isclose(soil_2.g_mod_at_m_eff_stress(m_eff), 36580544.6888, rtol=0.0001)


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
    assert soil_profile.layer_depth(2) == 4.0
    assert soil_profile.layer_height(2) == 4.0


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


def test_get_layer_index_by_depth():
    sl1 = models.Soil()
    sl2 = models.Soil()
    sp = models.SoilProfile()
    sp.add_layer(0, sl1)
    sp.add_layer(3, sl2)
    assert sp.get_layer_index_by_depth(0) == 1
    assert sp.get_layer_index_by_depth(1) == 1
    assert sp.get_layer_index_by_depth(3) == 2
    assert sp.get_layer_index_by_depth(4) == 2


def test_can_remove_layers():
    sl1 = models.Soil()
    sl2 = models.Soil()
    sl3 = models.Soil()
    sp = models.SoilProfile()
    sp.add_layer(0.0, sl1)
    sp.add_layer(3.0, sl2)
    sp.add_layer(5.0, sl3)
    assert sp.get_layer_index_by_depth(0) == 1
    assert sp.get_layer_index_by_depth(3.5) == 2
    assert sp.get_layer_index_by_depth(5.5) == 3
    sp.remove_layer(2)
    assert sp.get_layer_index_by_depth(3.5) == 1
    assert sp.get_layer_index_by_depth(5.5) == 2
    sp.add_layer(3.0, sl2)
    assert sp.get_layer_index_by_depth(3.5) == 2
    assert sp.get_layer_index_by_depth(5.5) == 3
    sp.remove_layer_at_depth(3.0)
    assert sp.get_layer_index_by_depth(3.5) == 1
    assert sp.get_layer_index_by_depth(5.5) == 2
    sp.add_layer(3.0, sl2)
    with pytest.raises(KeyError) as e:
        sp.remove_layer_at_depth(3.3)
    assert str(e.value) == "'Depth: 3.3 not found in [0.0, 3.0, 5.0]'"


def test_can_replace_layers():
    sl1 = models.Soil()
    sl2 = models.Soil()
    sl2.g_mod = 2.0
    sl3 = models.Soil()
    sl3.g_mod = 3.0
    sp = models.SoilProfile()
    sp.add_layer(0.0, sl1)
    sp.add_layer(3.0, sl2)
    assert np.isclose(sp.layer(2).g_mod, 2.0)
    sp.replace_layer(2, sl3)
    assert np.isclose(sp.layer(2).g_mod, 3.0)


def test_set_soil_ids_in_soil_profile():
    sl1 = models.Soil()
    sl2 = models.Soil()
    sp = models.SoilProfile()
    sp.add_layer(0, sl1)
    sp.add_layer(3, sl2)
    assert sp.layer(2).id is None
    sp.set_soil_ids_to_layers()
    assert sp.layer(2).id == 2


def test_get_parameter_at_depth_in_soil_profile():
    sl1 = models.Soil()
    sl1_gmod = 30e6
    sl1.g_mod = sl1_gmod
    sl2 = models.Soil()
    sl2_cohesion = 20e3
    sl2.cohesion = sl2_cohesion
    sp = models.SoilProfile()
    sp.add_layer(0, sl1)
    sp.add_layer(3, sl2)
    print(sp.get_parameter_at_depth(2, 'g_mod'))
    assert np.isclose(sp.get_parameter_at_depth(2, 'g_mod'), sl1_gmod)
    assert sp.get_parameter_at_depth(4, 'g_mod') is None
    assert np.isclose(sp.get_parameter_at_depth(4, 'cohesion'), sl2_cohesion)
    assert sp.get_parameter_at_depth(2, 'cohesion') is None


def test_get_parameters_at_depth_in_soil_profile():
    sl1 = models.Soil()
    sl1_gmod = 30e6
    sl1_unit_dry_weight = 16000
    sl1.g_mod = sl1_gmod
    sl1.unit_dry_weight = sl1_unit_dry_weight
    sl2 = models.Soil()
    sl2_cohesion = 20e3
    sl2.cohesion = sl2_cohesion
    sp = models.SoilProfile()
    sp.add_layer(0, sl1)
    sp.add_layer(3, sl2)
    vals_at_2 = sp.get_parameters_at_depth(2, ['g_mod', 'unit_dry_weight', 'cohesion'])
    vals_at_4 = sp.get_parameters_at_depth(4, ['g_mod', 'unit_dry_weight', 'cohesion'])
    assert np.isclose(vals_at_2['g_mod'], sl1_gmod)
    assert np.isclose(vals_at_2['unit_dry_weight'], sl1_unit_dry_weight)
    assert vals_at_2['cohesion'] is None
    assert vals_at_4['g_mod'] is None
    assert vals_at_4['unit_dry_weight'] is None
    assert np.isclose(vals_at_4['cohesion'], sl2_cohesion)


def test_get_soil_at_depth_in_soil_profile():
    sl1 = models.Soil()
    sl1_gmod = 30e6
    sl1_unit_dry_weight = 16000
    sl1.g_mod = sl1_gmod
    sl1.unit_dry_weight = sl1_unit_dry_weight
    sl2 = models.Soil()
    sl2_cohesion = 20e3
    sl2.cohesion = sl2_cohesion
    sp = models.SoilProfile()
    sp.add_layer(0, sl1)
    sp.add_layer(3, sl2)
    sl_at_2 = sp.get_soil_at_depth(2)
    sl_at_4 = sp.get_soil_at_depth(4)
    assert np.isclose(sl_at_2.g_mod, sl1_gmod)
    assert np.isclose(sl_at_2.unit_dry_weight, sl1_unit_dry_weight)
    assert sl_at_2.cohesion is None
    assert sl_at_4.g_mod is None
    assert sl_at_4.unit_dry_weight is None
    assert np.isclose(sl_at_4.cohesion, sl2_cohesion)


def test_soil_profile_split_simple_prop():
    sl1 = models.Soil()
    sl1_gmod = 30e6
    sl1_unit_dry_weight = 16000
    sl1.g_mod = sl1_gmod

    sl1.unit_dry_weight = sl1_unit_dry_weight
    sl2 = models.Soil()
    sl2_cohesion = 20e3
    sl2.cohesion = sl2_cohesion
    sp = models.SoilProfile()
    sp.add_layer(0, sl1)
    sp.add_layer(3, sl2)
    sp.height = 5
    sp.split_props(props=["cohesion"])
    assert len(sp.split['thickness']) == len(sp.split['cohesion'])
    assert None in sp.split['cohesion']
    sl1.cohesion = 0.0
    sp.split_props(props=["cohesion"])
    assert np.max(sp.split["cohesion"]) == 20e3


def test_soil_profile_split_complex():
    sl1 = models.Soil()
    sl1_gmod = 40e6
    sl1_unit_dry_weight = 16000
    sl1.g_mod = sl1_gmod

    sl1.unit_dry_weight = sl1_unit_dry_weight
    sl2 = models.Soil()
    sl2_cohesion = 20e3
    sl2.cohesion = sl2_cohesion
    sp = models.SoilProfile()
    sp.add_layer(0, sl1)
    sp.add_layer(3, sl2)
    sp.height = 5
    sp.split_props(props=["shear_vel"])
    assert len(sp.split['thickness']) == len(sp.split['shear_vel'])

    assert None in sp.split['shear_vel']
    sl2.g_mod = 40e6
    sp.layer(2).unit_dry_weight = sl1_unit_dry_weight
    sp.split_props(props=["shear_vel"])
    print(sp.split["shear_vel"])
    assert None not in sp.split['shear_vel']


def test_soil_profile_split_complex_stress_dependent():
    sl1 = models.Soil()
    sl1_gmod = 40e6
    sl1_unit_dry_weight = 16000
    sl1.g_mod = sl1_gmod

    sl1.unit_dry_weight = sl1_unit_dry_weight
    sl2 = models.StressDependentSoil()
    sl2.phi = 30.0

    sp = models.SoilProfile()
    sp.add_layer(0, sl1)
    sp.add_layer(3, sl2)
    sp.height = 5
    with pytest.raises(ValueError):
        sp.split_props(props=["shear_vel"])
    sl2.unit_dry_weight = 17000
    sp.split_props(props=["shear_vel"])
    assert len(sp.split['thickness']) == len(sp.split['shear_vel'])

    assert None in sp.split['shear_vel']
    sl2.g0_mod = 501
    sp.layer(2).unit_dry_weight = sl1_unit_dry_weight
    sp.split_props(props=["shear_vel"])
    assert None not in sp.split['shear_vel']



if __name__ == '__main__':
    # test_e_critical()
    test_soil_profile_split_complex_stress_dependent()
    # test_poissons_ratio_again()
    # test_reset_all()
    # test_override_fake_key()
    # test_can_compute_layer_depth()
    # test_get_layer_index_by_depth()
    # test_get_soil_at_depth_in_soil_profile()
    # test_soil_profile_vertical_effective_stress()
    # test_e_max_to_saturated_weight_setter()