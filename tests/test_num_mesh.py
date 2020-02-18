import sfsimodels as sm
import sfsimodels.num.mesh
import numpy as np


def test_two_d_mesh():
    vs = 150.0
    rho = 1.8
    g_mod = vs ** 2 * rho
    sl = sm.Soil(g_mod=g_mod, unit_dry_weight=rho * 9.8, poissons_ratio=0.3)
    sp = sm.SoilProfile()
    sp.add_layer(0, sl)
    sp.add_layer(5, sl)
    sp.add_layer(12, sl)
    sp.height = 18
    sp.x = 0
    sp2 = sm.SoilProfile()
    sp2.add_layer(0, sl)
    sp2.add_layer(7, sl)
    sp2.add_layer(12, sl)
    sp2.height = 20
    sp.x_angles = [0.0, 0.05, 0.0]
    sp2.x_angles = [0.0, 0.00, 0.0]

    fd = sm.RaftFoundation()
    fd.width = 2
    fd.depth = 0
    fd.length = 100
    tds = sm.TwoDSystem()
    tds.width = 40
    tds.height = 15
    tds.add_sp(sp, x=0)
    tds.add_sp(sp2, x=14)
    tds.x_surf = np.array([0, 10, 12, 40])
    tds.y_surf = np.array([0, 0, 2, 2])
    bd = sm.NullBuilding()
    bd.set_foundation(fd)
    tds.add_bd(bd, x=8)

    x_scale_pos = np.array([0, 5, 15, 30])
    x_scale_vals = np.array([2., 1.0, 2.0, 3.0])
    femesh = sm.num.mesh.FiniteElement2DMesh(tds, 0.3, x_scale_pos=x_scale_pos, x_scale_vals=x_scale_vals)
    x_ind = femesh.get_indexes_at_xs([4.])[0]
    y_ind = femesh.get_indexes_at_depths([1.99])[0]
    lay_id = femesh.soils[x_ind][y_ind]
    p_ind = femesh.profile_indys[x_ind]
    assert p_ind == 0
    assert lay_id == -1
    y_ind = femesh.get_indexes_at_depths([-8])[0]
    lay_id = femesh.soils[x_ind][y_ind]
    p_ind = femesh.profile_indys[x_ind]
    assert p_ind == 0
    assert lay_id == 2


if __name__ == '__main__':
    test_two_d_mesh()
