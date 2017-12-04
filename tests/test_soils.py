from sfsimodels import models


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


def test_soil():
    sl = models.Soil()

    sl.unit_dry_weight = 17000
    sl.unit_sat_weight = 18000
    print(sl.e_curr)
    assert sl.specific_gravity is None
    sl.e_curr = 0.7
    print(sl.specific_gravity)


if __name__ == '__main__':
    test_soil()