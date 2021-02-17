import numpy as np
import pytest

import sfsimodels as sm
from sfsimodels import models, exceptions


def test_add_layer_to_soil_profile():
    soil_profile = models.SoilProfile()
    soil = models.Soil()
    soil_profile.add_layer(3, soil)
    soil_profile.add_layer(5, soil)
    soil_profile.add_layer(2.5, soil)
    layer_order = [2.5, 3, 5]
    ind = 0
    for layer in soil_profile.layers:
        assert layer == layer_order[ind]
        ind += 1


def test_vertical_stress_soil_profile():
    soil_profile = models.SoilProfile()
    soil_profile.add_layer(0, models.Soil())
    soil_profile.add_layer(2, models.Soil())
    soil_profile.add_layer(5, models.Soil())
    unit_weights = [15000.0, 20000.0, 15000.0]
    counter = 0
    for depth in soil_profile.layers:
        soil_profile.layers[depth].unit_dry_weight = unit_weights[counter]
        counter += 1

    assert soil_profile.get_v_total_stress_at_depth(1) == 15000.0
    assert soil_profile.get_v_total_stress_at_depth(2) == 30000.0
    assert soil_profile.get_v_total_stress_at_depth(3) == 50000.0
    assert soil_profile.get_v_total_stress_at_depth(5) == 90000.0
    assert soil_profile.get_v_total_stress_at_depth(6) == 105000.0

    soil_profile.gwl = 3.0
    soil_profile.layer(2).unit_sat_weight = 21000
    assert soil_profile.get_v_eff_stress_at_depth(2) == 30000.0
    assert soil_profile.get_v_eff_stress_at_depth(4) == 61200.0
    soil_profile.layer(1).e_curr = 0.6
    soil_profile.layer(1).saturation = 1
    assert soil_profile.get_v_eff_stress_at_depth(4) == 68550.0


def test_soil_profile_vertical_total_stress():
    soil_1 = models.Soil()
    soil_1.phi = 33.
    soil_1.cohesion = 50000
    soil_1.unit_dry_weight = 18000
    soil_profile = models.SoilProfile()
    soil_profile.add_layer(0, soil_1)
    assert np.isclose(soil_profile.get_v_total_stress_at_depth(5), 5 * 18000, rtol=0.0001)
    soil_profile.gwl = 3.
    assert np.isclose(soil_profile.get_v_total_stress_at_depth(3), 3 * 18000, rtol=0.0001)
    with pytest.raises(exceptions.AnalysisError):
        soil_profile.get_v_eff_stress_at_depth(4)
    soil_profile.layer(1).unit_sat_weight = 21000
    expected = 3 * 18000 + 2 * 21000
    assert np.isclose(soil_profile.get_v_total_stress_at_depth(5), expected, rtol=0.0001)
    soil_2 = models.Soil()
    soil_2.phi = 33.
    soil_2.cohesion = 50000
    soil_2.unit_dry_weight = 16000

    # CONSIDER TWO LAYER SOIL PROFILE
    soil_profile.add_layer(4., soil_2)
    soil_profile.gwl = 10000  # Dry first
    assert np.isclose(soil_profile.get_v_total_stress_at_depth(5), 4 * 18000 + 1 * 16000, rtol=0.0001)
    soil_profile.gwl = 3.
    with pytest.raises(exceptions.AnalysisError):
        soil_profile.get_v_eff_stress_at_depth(5)
    soil_profile.layer(2).unit_sat_weight = 20000
    expected = 3 * 18000 + 1 * 21000 + 1 * 20000
    assert np.isclose(soil_profile.get_v_total_stress_at_depth(5), expected, rtol=0.0001)



def test_soil_profile_vertical_total_stress_w_surface_layer():
    soil_1 = models.Soil()
    soil_1.phi = 33.
    soil_1.cohesion = 50000
    soil_1.unit_dry_weight = 18000
    soil_profile = models.SoilProfile()

    soil_profile.add_layer(-3, sm.Soil())
    soil_profile.add_layer(-1, soil_1)
    sl = soil_profile.layer(1)
    assert np.isclose(soil_profile.get_v_total_stress_at_depth(5), 5 * 18000, rtol=0.0001)
    soil_profile.gwl = 3.
    assert np.isclose(soil_profile.get_v_total_stress_at_depth(3), 3 * 18000, rtol=0.0001)
    with pytest.raises(exceptions.AnalysisError):
        soil_profile.get_v_eff_stress_at_depth(4)
    sl_id = soil_profile.get_layer_index_by_depth(1.5)
    soil_profile.layer(sl_id).unit_sat_weight = 21000
    expected = 3 * 18000 + 2 * 21000
    assert np.isclose(soil_profile.get_v_total_stress_at_depth(5), expected, rtol=0.0001)
    soil_2 = models.Soil()
    soil_2.phi = 33.
    soil_2.cohesion = 50000
    soil_2.unit_dry_weight = 16000

    # CONSIDER TWO LAYER SOIL PROFILE
    soil_profile.add_layer(4., soil_2)
    soil_profile.gwl = 10000  # Dry first
    assert np.isclose(soil_profile.get_v_total_stress_at_depth(5), 4 * 18000 + 1 * 16000, rtol=0.0001)
    soil_profile.gwl = 3.
    with pytest.raises(exceptions.AnalysisError):
        soil_profile.get_v_eff_stress_at_depth(5)
    sl_id = soil_profile.get_layer_index_by_depth(4.5)
    soil_profile.layer(sl_id).unit_sat_weight = 20000
    expected = 3 * 18000 + 1 * 21000 + 1 * 20000
    assert np.isclose(soil_profile.get_v_total_stress_at_depth(5), expected, rtol=0.0001)


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
    assert np.isclose(soil_profile.get_v_eff_stress_at_depth(2), 2 * 18000, rtol=0.0001)
    with pytest.raises(exceptions.AnalysisError):
        soil_profile.get_v_eff_stress_at_depth(z_c)
    soil_1.unit_sat_weight = 21000
    expected_sigma_veff = (z_c - gwl) * (21000 - 9800) + gwl * 18000
    assert np.isclose(soil_profile.get_v_eff_stress_at_depth(z_c), expected_sigma_veff, rtol=0.0001)


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
    assert np.isclose(soil_profile.get_hydrostatic_pressure_at_depth(2), 0.0, rtol=0.0001)
    assert np.isclose(soil_profile.get_hydrostatic_pressure_at_depth(z_c), 9800, rtol=0.0001)


def test_stress_dependent_soil_g_mod():
    soil_1 = models.Soil()
    soil_1.poissons_ratio = 0.33
    soil_1.unit_dry_weight = 18000
    soil_1.specific_gravity = 2.65
    soil_2 = sm.StressDependentSoil()
    soil_2.poissons_ratio = 0.33
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
    assert np.isclose(soil_profile.get_hydrostatic_pressure_at_depth(z_c), 9800, rtol=0.0001)
    v_eff = soil_profile.get_v_eff_stress_at_depth(z_c)
    assert np.isclose(soil_2.get_g_mod_at_v_eff_stress(v_eff), 37285488.97326168, rtol=0.0001)
    k_0 = soil_2.poissons_ratio / (1 - soil_2.poissons_ratio)
    m_eff = v_eff * (1 + 2 * k_0) / 3
    assert np.isclose(soil_2.get_g_mod_at_m_eff_stress(m_eff), 37285488.97326168, rtol=0.0001)


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


def test_can_move_layer():
    sl1 = models.Soil()
    sl2 = models.Soil()
    sp = models.SoilProfile()
    sp.add_layer(0.0, sl1)
    sp.add_layer(3.0, sl2)
    assert sp.get_layer_depth(2) == 3.0
    sp.move_layer(4.0, 2)
    assert sp.get_layer_depth(2) == 4.0


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
    sp.gen_split(props=["cohesion"])
    assert len(sp.split['thickness']) == len(sp.split['cohesion'])
    assert None in sp.split['cohesion']
    sl1.cohesion = 0.0
    sp.gen_split(props=["cohesion"])
    assert np.max(sp.split["cohesion"]) == 20e3


def test_soil_profile_split_simple_shear_vel():
    sl1 = models.Soil()
    sl1_gmod = 30e6
    sl1_unit_dry_weight = 16000
    sl1.g_mod = sl1_gmod
    sl1.unit_dry_weight = sl1_unit_dry_weight

    sl2 = models.Soil()
    sl2_gmod = 20e3
    sl2_unit_dry_weight = 16000
    sl2.unit_dry_weight = sl2_unit_dry_weight
    sl2.g_mod = sl2_gmod

    sp = models.SoilProfile()
    sp.add_layer(0, sl1)
    sp.add_layer(3, sl2)
    sp.height = 5
    t = sp.layer_height(1) / sp.layer(1).get_shear_vel(saturated=False) + \
        sp.layer_height(2) / sp.layer(2).get_shear_vel(saturated=False)
    sp.gen_split(props=["shear_vel"])
    t_split = np.sum(sp.split['thickness'] / sp.split['shear_vel'])
    assert np.isclose(t, t_split)


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
    sp.gen_split(props=["shear_vel"])
    assert len(sp.split['thickness']) == len(sp.split['shear_vel'])

    assert None in sp.split['shear_vel']
    sl2.g_mod = 40e6
    sp.layer(2).unit_dry_weight = sl1_unit_dry_weight
    sp.gen_split(props=["shear_vel"])
    assert None not in sp.split['shear_vel']


def test_soil_profile_split_complex_stress_dependent():
    sl1 = models.Soil()
    sl1_gmod = 40e6
    sl1_unit_dry_weight = 16000
    sl1.g_mod = sl1_gmod

    sl1.unit_dry_weight = sl1_unit_dry_weight
    sl2 = models.StressDependentSoil()
    sl2.poissons_ratio = 0.33

    sp = models.SoilProfile()
    sp.add_layer(0, sl1)
    sp.add_layer(3, sl2)
    sp.height = 5
    with pytest.raises(ValueError):
        sp.gen_split(props=["shear_vel"])
    sl2.unit_dry_weight = 17000
    sp.gen_split(props=["shear_vel"])
    assert len(sp.split['thickness']) == len(sp.split['shear_vel'])

    assert None in sp.split['shear_vel']
    sl2.g0_mod = 501
    sp.layer(2).unit_dry_weight = sl1_unit_dry_weight
    sp.gen_split(props=["shear_vel"])
    assert None not in sp.split['shear_vel']


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
    ecp_output.add_to_dict(sp, export_none=False)
    p_str = ecp_output.to_str()
    objs = sm.loads_json(p_str, verbose=0)
    loaded_soil = objs['soils'][1]
    load_soil_from_profile = sp.layer(1)
    assert np.isclose(loaded_soil.g_mod, sl1.g_mod)
    assert np.isclose(load_soil_from_profile.g_mod, sl1.g_mod)


if __name__ == '__main__':
    test_save_and_load_soil_profile()
