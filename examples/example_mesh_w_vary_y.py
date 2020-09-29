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
sp.add_layer(3.4, sl2)
sp.add_layer(5.7, sl3)
sp2 = sm.SoilProfile()
sp2.add_layer(0, sl4)
sp2.add_layer(3.9, sl5)
sp2.add_layer(6.5, sl0)
sp2.height = 20
sp.x_angles = [0.17, 0.07, 0.0]
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

show_set_init_y_blocks = 0
show_ecp_definition = 0
show_get_special_coords_and_slopes = 0
show_adjust_blocks_to_be_consistent_with_slopes = 0
show_trim_grid_to_target_dh = 0
show_build_req_y_node_positions = 0
##%
fc = mesh2d_vary_y.FiniteElementVaryY2DMeshConstructor(tds, 0.5, x_scale_pos=x_scale_pos,
                                                       x_scale_vals=x_scale_vals, auto_run=False)

if show_ecp_definition:
    win = pg.plot()
    win.setMinimumSize(900, 300)
    win.setWindowTitle('ECP definition')
    win.setXRange(0, tds.width)
    win.setYRange(-tds.height, max(tds.y_surf))
    o3plot.plot_two_d_system(win, tds)
    o3plot.show()

##%
fc.get_special_coords_and_slopes()  # Step 1
if show_get_special_coords_and_slopes:
    win = pg.plot()
    win.setMinimumSize(900, 300)
    win.setWindowTitle('get_special_coords_and_slopes')
    win.setXRange(0, tds.width)
    win.setYRange(-tds.height, max(tds.y_surf))
    y_sps_surf = np.interp(tds.x_sps, tds.x_surf, tds.y_surf)

    for i in range(len(tds.sps)):
        x0 = tds.x_sps[i]
        if i == len(tds.sps) - 1:
            x1 = tds.width
        else:
            x1 = tds.x_sps[i + 1]
        xs = np.array([x0, x1])
        x_angles = list(tds.sps[i].x_angles)
        sp = tds.sps[i]
        for ll in range(1, sp.n_layers + 1):
            ys = y_sps_surf[i] - sp.layer_depth(ll) + x_angles[ll - 1] * (xs - x0)
            win.plot(xs, ys, pen='w')
    for i in range(len(fc.sds)):
        win.plot(fc.sds[i][0], fc.sds[i][1], pen='b')
    win.plot([0, fc.tds.width], [-fc.tds.height, -fc.tds.height], pen='w')
    xcs = fc.xcs_sorted
    for i in range(len(xcs)):
        xc = xcs[i]
        xn = xc * np.ones_like(list(fc.yd[xc]))
        win.plot(xn, list(fc.yd[xc]), symbol='o', symbolPen='r')

    o3plot.show()

##%
fc.set_init_y_blocks()
if show_set_init_y_blocks:
    win = pg.plot()
    win.setMinimumSize(900, 300)
    win.setWindowTitle('set_init_y_blocks')
    win.setXRange(0, tds.width)
    win.setYRange(-tds.height, max(tds.y_surf))
    for i in range(len(fc.sds)):
        win.plot(fc.sds[i][0], fc.sds[i][1], pen='b')
    win.plot([0, fc.tds.width], [-fc.tds.height, -fc.tds.height], pen='w')
    xcs = fc.xcs_sorted
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

##%
fc.adjust_blocks_to_be_consistent_with_slopes()  # TODO: Add back add
if show_adjust_blocks_to_be_consistent_with_slopes:
    win = pg.plot()
    win.setMinimumSize(900, 300)
    win.setWindowTitle('adjust_blocks_to_be_consistent_with_slopes')
    win.setXRange(0, tds.width)
    win.setYRange(-tds.height, max(tds.y_surf))
    for i in range(len(fc.sds)):
        win.plot(fc.sds[i][0], fc.sds[i][1], pen='b')
    win.plot([0, fc.tds.width], [-fc.tds.height, -fc.tds.height], pen='w')
    xcs = fc.xcs_sorted
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
        nbs = np.cumsum(fc.y_blocks[xc])
        for cc in range(len(fc.y_blocks[xc])):
            text = pg.TextItem(f'{nbs[cc]}', anchor=(0, 1))
            win.addItem(text)
            text.setPos(xc, fc.yd[xc][cc+1])
        xn = xc * np.ones_like(y_node_coords)
        win.plot(xn, y_node_coords, symbol='+')
        win.addItem(pg.InfiniteLine(xcs[i], angle=90, pen=(0, 255, 0, 100)))

    o3plot.show()
##%
fc.trim_grid_to_target_dh()
if show_trim_grid_to_target_dh:
    win = pg.plot()
    win.setMinimumSize(900, 300)
    win.setWindowTitle('trim_grid_to_target_dh')
    win.setXRange(0, tds.width)
    win.setYRange(-tds.height, max(tds.y_surf))
    for i in range(len(fc.sds)):
        win.plot(fc.sds[i][0], fc.sds[i][1], pen='b')
    win.plot([0, fc.tds.width], [-fc.tds.height, -fc.tds.height], pen='w')
    xcs = fc.xcs_sorted
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
        nbs = np.cumsum(fc.y_blocks[xc])
        for cc in range(len(fc.y_blocks[xc])):
            text = pg.TextItem(f'{nbs[cc]}', anchor=(0, 1))
            win.addItem(text)
            text.setPos(xc, fc.yd[xc][cc + 1])
        xn = xc * np.ones_like(y_node_coords)
        win.plot(xn, y_node_coords, symbol='+')
        win.addItem(pg.InfiniteLine(xcs[i], angle=90, pen=(0, 255, 0, 100)))

    o3plot.show()

##%
fc.build_req_y_node_positions()
if show_build_req_y_node_positions:
    win = pg.plot()
    win.setMinimumSize(900, 300)
    win.setWindowTitle('build_req_y_node_positions')
    win.setXRange(0, tds.width)
    win.setYRange(-tds.height, max(tds.y_surf))
    o3plot.plot_two_d_system(win, tds)
    xcs = fc.xcs_sorted
    for i in range(len(xcs)):
        xc = xcs[i]
        h_blocks = np.diff(fc.yd[xc])
        dhs = h_blocks / fc.y_blocks[xc]
        y_node_steps = [0]
        for hh in range(len(fc.y_blocks[xc])):
            y_node_steps += [dhs[hh] for u in range(fc.y_blocks[xc][hh])]
        y_node_coords = np.cumsum(y_node_steps) - tds.height

        xn = xc * np.ones_like(list(fc.req_y_coords_at_xcs[i]))
        win.plot(xn, list(fc.req_y_coords_at_xcs[i]), symbol='x', symbolPen='r')
        win.addItem(pg.InfiniteLine(xcs[i], angle=90, pen=(0, 255, 0, 100)))

    o3plot.show()

##%
fc.build_y_coords_at_xcs()
show_build_y_coords_grid_via_propagation = 0
if show_build_y_coords_grid_via_propagation:
    win = pg.plot()
    win.setMinimumSize(900, 300)
    win.setWindowTitle('build_y_coords_at_xcs')
    win.setXRange(0, tds.width)
    win.setYRange(-tds.height, max(tds.y_surf))
    for i in range(len(fc.sds)):
        win.plot(fc.sds[i][0], fc.sds[i][1], pen='b')
    win.plot([0, fc.tds.width], [-fc.tds.height, -fc.tds.height], pen='w')
    xcs = fc.xcs_sorted
    for i in range(len(xcs)):
        xc = xcs[i]
        h_blocks = np.diff(fc.yd[xc])
        dhs = h_blocks / fc.y_blocks[xc]
        y_node_steps = [0]
        for hh in range(len(fc.y_blocks[xc])):
            y_node_steps += [dhs[hh] for u in range(fc.y_blocks[xc][hh])]
        y_node_coords = np.cumsum(y_node_steps) - tds.height
        xn = xc * np.ones_like(list(fc.req_y_coords_at_xcs[i]))
        win.plot(xn, list(fc.req_y_coords_at_xcs[i]), symbol='x', symbolPen='y')
        xn = xc * np.ones_like(list(fc.y_coords_at_xcs[i]))
        win.plot(xn, list(fc.y_coords_at_xcs[i]), symbol='+', symbolPen='r')
        win.addItem(pg.InfiniteLine(xcs[i], angle=90, pen=(0, 255, 0, 100)))

    o3plot.show()


##%
fc.set_x_nodes()
show_set_x_nodes = 0
if show_set_x_nodes:
    win = pg.plot()
    win.setMinimumSize(900, 300)
    win.setWindowTitle('set_x_nodes')
    win.setXRange(0, tds.width)
    win.setYRange(-tds.height, max(tds.y_surf))
    for i in range(len(fc.sds)):
        win.plot(fc.sds[i][0], fc.sds[i][1], pen='b')
    win.plot([0, fc.tds.width], [-fc.tds.height, -fc.tds.height], pen='w')
    for i in range(len(fc.x_nodes)):
        win.addItem(pg.InfiniteLine(fc.x_nodes[i], angle=90, pen='r'))
    for i in range(len(fc.xcs_sorted)):
        win.addItem(pg.InfiniteLine(fc.xcs_sorted[i], angle=90, pen=(0, 255, 0, 100)))

    o3plot.show()


##%
fc.build_y_coords_grid_via_propagation()
show_build_y_coords_grid_via_propagation = 1
if show_build_y_coords_grid_via_propagation:
    win = pg.plot()
    win.setMinimumSize(900, 300)
    win.setWindowTitle('build_y_coords_grid_via_propagation')
    win.setXRange(0, tds.width)
    win.setYRange(-tds.height, max(tds.y_surf))
    for i in range(len(fc.sds)):
        win.plot(fc.sds[i][0], fc.sds[i][1], pen='b')
    win.plot([0, fc.tds.width], [-fc.tds.height, -fc.tds.height], pen='w')
    xns = fc.x_nodes
    for i in range(len(xns)):
        xc = xns[i]
        xn = xc * np.ones_like(fc.y_nodes[i])
        win.plot(xn, fc.y_nodes[i], pen=None, symbol='o', symbolPen='r', symbolBrush='r', symbolSize=3)
    for i in range(len(fc.xcs_sorted)):
        win.addItem(pg.InfiniteLine(fc.xcs_sorted[i], angle=90, pen=(0, 255, 0, 100)))
    o3plot.show()

##%
show_set_to_decimal_places = 1
if show_set_to_decimal_places:
    win = pg.plot()
    win.setMinimumSize(900, 300)
    win.setWindowTitle('set_to_decimal_places')
    win.setXRange(0, tds.width)
    win.setYRange(-tds.height, max(tds.y_surf))
    for i in range(len(fc.sds)):
        win.plot(fc.sds[i][0], fc.sds[i][1], pen='b')
    win.plot([0, fc.tds.width], [-fc.tds.height, -fc.tds.height], pen='w')
    xns = fc.x_nodes
    for i in range(len(xns)):
        xc = xns[i]
        xn = xc * np.ones_like(fc.y_nodes[i])
        win.plot(xn, fc.y_nodes[i], pen=None, symbol='o', symbolPen=0.5, symbolBrush=0.5, symbolSize=3)
    for i in range(len(fc.xcs_sorted)):
        win.addItem(pg.InfiniteLine(fc.xcs_sorted[i], angle=90, pen=(0, 255, 0, 100)))
fc.dp = 2
fc.set_to_decimal_places()
if show_set_to_decimal_places:
    xns = fc.x_nodes
    for i in range(len(xns)):
        xc = xns[i]
        xn = xc * np.ones_like(fc.y_nodes[i])
        win.plot(xn, fc.y_nodes[i], pen=None, symbol='o', symbolPen='r', symbolBrush='r', symbolSize=3)
    for i in range(len(fc.xcs_sorted)):
        win.addItem(pg.InfiniteLine(fc.xcs_sorted[i], angle=90, pen=(0, 255, 0, 100)))
    o3plot.show()

##%
fc.set_soil_ids_to_grid()
fc.create_mesh()
show = 0
if show:
    win = pg.plot()
    win.setMinimumSize(900, 300)
    win.setWindowTitle('ECP definition')
    win.setXRange(0, tds.width)
    win.setYRange(-tds.height, max(tds.y_surf))
    for i in range(len(fc.sds)):
        win.plot(fc.sds[i][0], fc.sds[i][1], pen='b')
    win.plot([0, fc.tds.width], [-fc.tds.height, -fc.tds.height], pen='w')
    # for i in range(len(fc.x_nodes)):
    #     win.addItem(pg.InfiniteLine(fc.x_nodes[i], angle=90, pen='r'))
    o3plot.plot_finite_element_mesh_onto_win(win, fc.femesh)
    o3plot.show()

##%
fc.exclude_fd_eles()
show = 0
if show:
    win = pg.plot()
    win.setMinimumSize(900, 300)
    win.setWindowTitle('ECP definition')
    win.setXRange(0, tds.width)
    win.setYRange(-tds.height, max(tds.y_surf))
    for i in range(len(fc.sds)):
        win.plot(fc.sds[i][0], fc.sds[i][1], pen='b')
    win.plot([0, fc.tds.width], [-fc.tds.height, -fc.tds.height], pen='w')
    # for i in range(len(fc.x_nodes)):
    #     win.addItem(pg.InfiniteLine(fc.x_nodes[i], angle=90, pen='r'))
    o3plot.plot_finite_element_mesh_onto_win(win, fc.femesh)
    o3plot.show()