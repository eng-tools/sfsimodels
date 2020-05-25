from sfsimodels.models import loads


def test_loads_add_and_remove():
    load = loads.Load(p_x=10)
    assert load.p_x == 10
    assert load.p_y is None
    load.p_x = 15
    load.p_y = 9
    assert load.p_x == 15
    assert load.p_y == 9
    load.p_z = 3
    load.t_xx = 4
    load.t_yy = 5
    load.t_zz = 6
    assert load.p_z == 3
    assert load.t_xx == 4
    assert load.t_yy == 5
    assert load.t_zz == 6


def test_load_at_coords_add_and_remove():
    load = loads.LoadAtCoords(p_x=10, x=3)
    assert load.p_x == 10
    assert load.p_y is None
    load.p_x = 15
    load.p_y = 9
    assert load.p_x == 15
    assert load.p_y == 9
    load.p_z = 3
    load.t_xx = 4
    load.t_yy = 5
    load.t_zz = 6
    assert load.p_z == 3
    assert load.t_xx == 4
    assert load.t_yy == 5
    assert load.t_zz == 6
    assert load.x == 3
