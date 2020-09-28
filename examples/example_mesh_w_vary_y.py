##%
import sfsimodels as sm
from sfsimodels.num.mesh import mesh2d_vary_y
import numpy as np
import sys
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
import o3plot

#%%
vs = 150.0
rho = 1.8
g_mod = vs ** 2 * rho

sl0 = sm.Soil(g_mod=g_mod, unit_dry_weight=rho * 9.8, poissons_ratio=0.31)
sl1 = sm.Soil(g_mod=g_mod, unit_dry_weight=rho * 9.8, poissons_ratio=0.32)
sl2 = sm.Soil(g_mod=g_mod, unit_dry_weight=rho * 9.8, poissons_ratio=0.33)
sl3 = sm.Soil(g_mod=g_mod, unit_dry_weight=rho * 9.8, poissons_ratio=0.34)
sl4 = sm.Soil(g_mod=g_mod, unit_dry_weight=rho * 9.8, poissons_ratio=0.35)
sl5 = sm.Soil(g_mod=g_mod, unit_dry_weight=rho * 9.8, poissons_ratio=0.36)
sp = sm.SoilProfile()
h_face = 1.8
sp.add_layer(0, sl1)
sp.add_layer(3.5, sl2)
sp.add_layer(5.7, sl3)
sp2 = sm.SoilProfile()
sp2.add_layer(0, sl4)
sp2.add_layer(3.7, sl5)
sp2.add_layer(6.5, sl0)
sp2.height = 20
sp.x_angles = [0.2, 0.07, 0.0]
sp2.x_angles = [0.0, 0.00, 0.0]

fd = sm.RaftFoundation()
fd.width = 3
fd.depth = 0.6
fd.ip_axis = 'width'
fd.height = 0.7
fd.length = 100
tds = sm.TwoDSystem(width=30, height=7.5)
tds.add_sp(sp, x=0)
tds.add_sp(sp2, x=17)
tds.x_surf = np.array([0, 12, 14, tds.width])
tds.y_surf = np.array([0, 0, h_face, h_face])
bd = sm.NullBuilding()
bd.set_foundation(fd, x=0.0)
tds.add_bd(bd, x=20)

x_scale_pos = np.array([0, 5, 15, 30])
x_scale_vals = np.array([2., 1.0, 2.0, 3.0])
##%
fc = mesh2d_vary_y.FiniteElementVaryY2DMeshConstructor(tds, 0.5, x_scale_pos=x_scale_pos,
                                                       x_scale_vals=x_scale_vals, auto_run=False)
show = 0
if show:
    win = pg.plot()
    win.setMinimumSize(900, 300)
    win.setWindowTitle('ECP definition')
    win.setXRange(0, tds.width)
    win.setYRange(-tds.height, max(tds.y_surf))
    o3plot.plot_two_d_system(win, tds)
    # o3plot.plot_finite_element_mesh_onto_win(win, femesh)

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
##%
fc.get_special_coords_and_slopes()  # Step 1
xcs = list(fc.yd)
xcs.sort()
xcs = np.array(xcs)
show = 0
if show:
    win = pg.plot()
    win.setMinimumSize(900, 300)
    win.setWindowTitle('ECP definition')
    win.setXRange(0, tds.width)
    win.setYRange(-tds.height, max(tds.y_surf))
    o3plot.plot_two_d_system(win, tds)
    # o3plot.plot_finite_element_mesh_onto_win(win, femesh)
    for i in range(len(xcs)):
        win.addItem(pg.InfiniteLine(xcs[i], angle=90, pen=(0, 255, 0, 100)))

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()

##%
fc.set_init_y_blocks()
show = 1
if show:
    win = pg.plot()
    win.setMinimumSize(900, 300)
    win.setWindowTitle('ECP definition')
    win.setXRange(0, tds.width)
    win.setYRange(-tds.height, max(tds.y_surf))
    o3plot.plot_two_d_system(win, tds)
    y_node_nums_at_xcs = [list(np.cumsum(fc.y_blocks[xcs])) for xcs in fc.y_blocks]

    for i in range(len(xcs)):
        xc = xcs[i]
        h_blocks = np.diff(fc.yd[xc])
        dhs = h_blocks / fc.y_blocks[xc]
        y_node_steps = [0]
        for hh in range(len(fc.y_blocks[xc])):
            y_node_steps += [dhs[hh] for u in range(fc.y_blocks[xc][hh])]
        y_node_coords = np.cumsum(y_node_steps) - tds.height
        xn = xc * np.ones_like(list(fc.yd[xc]))
        win.plot(xn, list(fc.yd[xc]), symbol='o', pen='r')
        xn = xc * np.ones_like(y_node_coords)
        win.plot(xn, y_node_coords, symbol='+')
        win.addItem(pg.InfiniteLine(xcs[i], angle=90, pen=(0, 255, 0, 100)))

    o3plot.show()


