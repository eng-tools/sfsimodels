import sfsimodels as sm
import json
import numpy as np


def test_save_and_load_2d_system():

    ref_press = 100.e3
    vs = 250.0

    sl = sm.Soil()
    unit_mass = 1700.0
    sl.g_mod = vs ** 2 * unit_mass
    sl.poissons_ratio = 0.0
    # sl.cohesion = sl.g_mod / 1000
    sl.cohesion = 30.0e3
    sl.phi = 0.0
    sl.unit_dry_weight = unit_mass * 9.8
    sl.specific_gravity = 2.65
    sl.xi = 0.03  # for linear analysis
    sl.sra_type = 'hyperbolic'
    sl.inputs += [ 'sra_type', 'xi']
    sp = sm.SoilProfile()
    sp.add_layer(0.0, sl)
    sp.height = 1e3
    sp.x_angles = [0.0, 0.0]
    fd = sm.RaftFoundation()
    fd.width = 2
    fd.depth = 0.8
    fd.height = 1
    fd.length = 100
    fd.ip_axis = 'width'
    bd = sm.SDOFBuilding()
    bd.h_eff = 8.
    bd.set_foundation(fd, x=0.0)
    sys_width = 6 * fd.width
    tds = sm.TwoDSystem(width=sys_width, height=10)
    tds.add_sp(sp, 0)
    tds.add_bd(bd, sys_width / 2)
    tds.id = 1
    ecp_out = sm.Output()
    ecp_out.add_to_dict(tds)
    p_str = json.dumps(ecp_out.to_dict(), skipkeys=["__repr__"], indent=4)
    objs = sm.loads_json(p_str)
    building = objs["building"][1]
    foundation = objs["foundation"][1]
    assert np.isclose(building.h_eff, 8)
    assert np.isclose(building.fd.height, 1)


if __name__ == '__main__':
    test_save_and_load_2d_system()