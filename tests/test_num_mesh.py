import sfsimodels as sm
import sfsimodels.num.mesh
import numpy as np


def test_two_d_mesh():
    rho = 1.8
    sl1 = sm.Soil(g_mod=50, unit_dry_weight=rho * 9.8, poissons_ratio=0.3)
    sl2 = sm.Soil(g_mod=100, unit_dry_weight=rho * 9.8, poissons_ratio=0.3)
    sl3 = sm.Soil(g_mod=400, unit_dry_weight=rho * 9.8, poissons_ratio=0.3)
    sl4 = sm.Soil(g_mod=600, unit_dry_weight=rho * 9.8, poissons_ratio=0.3)
    sp = sm.SoilProfile()
    sp.add_layer(0, sl1)
    sp.add_layer(5, sl2)
    sp.add_layer(12, sl3)
    sp.height = 18
    sp.x = 0
    sp2 = sm.SoilProfile()
    sp2.add_layer(0, sl1)
    sp2.add_layer(7, sl4)
    sp2.add_layer(12, sl3)
    sp2.height = 20
    sp.x_angles = [0.0, 0.05, 0.0]
    sp2.x_angles = [0.0, 0.00, 0.0]

    fd = sm.RaftFoundation()
    fd.width = 2
    fd.depth = 0
    fd.length = 100
    tds = sm.TwoDSystem(40, 15)
    tds.add_sp(sp, x=0)
    tds.add_sp(sp2, x=14)
    tds.x_surf = np.array([0, 10, 12, 40])
    tds.y_surf = np.array([0, 0, 2, 2])
    bd = sm.NullBuilding()
    bd.set_foundation(fd)
    bd_x = 8.
    tds.add_bd(bd, x=bd_x)

    x_scale_pos = np.array([0, 5, 15, 30])
    x_scale_vals = np.array([2., 1.0, 2.0, 3.0])
    femesh = sm.num.mesh.FiniteElement2DMesh(tds, 0.3, x_scale_pos=x_scale_pos, x_scale_vals=x_scale_vals)

    x_ind = femesh.get_indexes_at_xs([4.])[0]
    y_ind = femesh.get_indexes_at_depths([1.99])[0]
    sl_ind = femesh.soil_grid[x_ind][y_ind]
    assert sl_ind == 1000000
    assert femesh.active_nodes[x_ind][y_ind] == 0
    p_ind = femesh.profile_indys[x_ind]
    assert p_ind == 0
    y_ind = femesh.get_indexes_at_depths([-3])[0]
    sl_ind = femesh.soil_grid[x_ind][y_ind]
    assert femesh.soils[sl_ind].g_mod == 50
    y_ind = femesh.get_indexes_at_depths([-8])[0]
    sl_ind = femesh.soil_grid[x_ind][y_ind]
    assert femesh.soils[sl_ind].g_mod == 100
    y_ind = femesh.get_indexes_at_depths([-12.5])[0]
    sl_ind = femesh.soil_grid[x_ind][y_ind]
    assert femesh.soils[sl_ind].g_mod == 400
    assert femesh.active_nodes[x_ind][y_ind] == 1

    x_ind = femesh.get_indexes_at_xs([16.])[0]
    p_ind = femesh.profile_indys[x_ind]
    assert p_ind == 1
    y_ind = femesh.get_indexes_at_depths([1.99])[0]
    sl_ind = femesh.soil_grid[x_ind][y_ind]
    assert femesh.soils[sl_ind].g_mod == 50
    y_ind = femesh.get_indexes_at_depths([-3])[0]
    sl_ind = femesh.soil_grid[x_ind][y_ind]
    assert femesh.soils[sl_ind].g_mod == 50
    y_ind = femesh.get_indexes_at_depths([-8])[0]
    sl_ind = femesh.soil_grid[x_ind][y_ind]
    assert femesh.soils[sl_ind].g_mod == 600
    y_ind = femesh.get_indexes_at_depths([-12.5])[0]
    sl_ind = femesh.soil_grid[x_ind][y_ind]
    assert femesh.soils[sl_ind].g_mod == 400

    # check foundation
    lhs_ind = np.argmin(abs(femesh.x_nodes - bd_x))
    assert np.isclose(bd_x, femesh.x_nodes[lhs_ind]), femesh.x_nodes[lhs_ind]
    rhs_ind = np.argmin(abs(femesh.x_nodes - bd_x - fd.width))
    assert np.isclose(bd_x + fd.width, femesh.x_nodes[rhs_ind])


def test_two_d_mesh_w_1_profile():
    rho = 1.8
    sl1 = sm.Soil(g_mod=50, unit_dry_weight=rho * 9.8, poissons_ratio=0.3)
    sl2 = sm.Soil(g_mod=100, unit_dry_weight=rho * 9.8, poissons_ratio=0.3)
    sl3 = sm.Soil(g_mod=400, unit_dry_weight=rho * 9.8, poissons_ratio=0.3)
    sp = sm.SoilProfile()
    sp.add_layer(0, sl1)
    sp.add_layer(5, sl2)
    sp.add_layer(12, sl3)
    sp.x_angles = [0.0, 0.0, 0.0]
    sp.height = 18
    sp.x = 0

    tds = sm.TwoDSystem(4, 15)
    tds.add_sp(sp, x=0)
    tds.x_surf = np.array([0])
    tds.y_surf = np.array([0])

    x_scale_pos = np.array([0])
    x_scale_vals = np.array([2.])
    femesh = sm.num.mesh.FiniteElement2DMesh(tds, 0.3, x_scale_pos=x_scale_pos, x_scale_vals=x_scale_vals)
    ind = np.argmin(abs(femesh.y_nodes + 5.0))
    assert np.isclose(-5.0, femesh.y_nodes[ind])
    ind = np.argmin(abs(femesh.y_nodes + 12.0))
    assert np.isclose(-12.0, femesh.y_nodes[ind])
    ind = np.argmin(abs(femesh.y_nodes + 15.0))
    assert np.isclose(-15.0, femesh.y_nodes[ind])


if __name__ == '__main__':
    test_two_d_mesh()
