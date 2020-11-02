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
sp2.add_layer(3.9, sl2)
sp2.add_layer(6.5, sl5)
sp2.height = 20
sp.x_angles = [None, 0.07, 0.0]
sp2.x_angles = [None, 0.00, 0.0]


tds = sm.TwoDSystem(width=45, height=7.5)
tds.add_sp(sp, x=0)
tds.add_sp(sp2, x=17)
tds.x_surf = np.array([0, 12, 13, 20, 25, tds.width])
tds.y_surf = np.array([0, 0, h_face, h_face-0.6, h_face-0.3, h_face + 0.])
# tds.x_surf = np.array([0, 20, 21, tds.width])
# tds.y_surf = np.array([h_face-0.9, h_face, 0, 0.])

x_scale_pos = np.array([0, 5, 10, 16, 19, 25, 29])
x_scale_vals = np.array([2., 1.2, 1.0, 1.2, 0.7, 1.2, 2])

show_set_init_y_blocks = 0
show_ecp_definition = 0
show_get_special_coords_and_slopes = 1
show_adjust_blocks_to_be_consistent_with_slopes = 0
show_trim_grid_to_target_dh = 0
show_build_req_y_node_positions = 0
show_set_x_nodes = 0
show_build_y_coords_grid_via_propagation = 0
show_set_to_decimal_places = 0
show_smooth_surf = 1
show_set_soil_ids_to_grid = 1
show_exclude_fd_eles = 0
##%
fc = mesh2d_vary_y.FiniteElementVary2DMeshConstructor(tds, 0.5, x_scale_pos=x_scale_pos,
                                                       x_scale_vals=x_scale_vals, auto_run=False)

if show_ecp_definition:
    win = o3plot.create_scaled_window_for_tds(tds, title='ECP definition')
    o3plot.plot_two_d_system(win, tds)
    o3plot.show()

##%
fc.get_special_coords_and_slopes()  # Step 1
if show_get_special_coords_and_slopes:
    win = o3plot.create_scaled_window_for_tds(tds, title='get_special_coords_and_slopes')
    leg = win.addLegend(offset=(70, 30), brush=0.3, labelTextColor='w')
    o3plot.plot_two_d_system(tds, win, c2='w', cs='w')
    leg.addItem(pg.PlotDataItem([0], [0], pen='w'), name='2D system definition')
    for i in range(len(fc.sds)):
        win.plot(fc.sds[i][0], fc.sds[i][1], pen='b', symbol='x', symbolPen='b', symbolBrush='b', symbolSize=10, name='Important slope')
    xcs = fc.xcs_sorted
    for i in range(len(xcs)):
        xc = xcs[i]
        xn = xc * np.ones_like(list(fc.yd[xc]))
        win.plot(xn, list(fc.yd[xc]), symbol='o', symbolPen='r', symbolBrush='r', symbolSize=5, pen=None, name='Important coordinates')
    o3plot.revamp_legend(leg)
    o3plot.show()

##%
fc.set_init_y_blocks()
if show_set_init_y_blocks:
    win = o3plot.create_scaled_window_for_tds(tds, title='set_init_y_blocks')
    leg = win.addLegend(offset=(70, 30), brush=0.3, labelTextColor='w')
    o3plot.plot_two_d_system(tds, win, c2='w', cs='w')
    leg.addItem(pg.PlotDataItem([0], [0], pen='w'), name='2D system definition')
    for i in range(len(fc.sds)):
        win.plot(fc.sds[i][0], fc.sds[i][1], pen='y', name='Important slope')
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
        win.plot(xn, list(fc.yd[xc]), symbol='o', symbolPen='y', symbolBrush='y', symbolSize=5, pen=None, name='Important coordinates')
        xn = xc * np.ones_like(y_node_coords)
        win.plot(xn, y_node_coords, symbol='+', name='approximate element')
        win.addItem(pg.InfiniteLine(xcs[i], angle=90, pen=(0, 255, 0, 100)))
    o3plot.revamp_legend(leg)
    o3plot.show()

##%
fc.adjust_blocks_to_be_consistent_with_slopes()
if show_adjust_blocks_to_be_consistent_with_slopes:
    win = o3plot.create_scaled_window_for_tds(tds, title='adjust_blocks_to_be_consistent_with_slopes')
    leg = win.addLegend(offset=(70, 30), brush=0.3, labelTextColor='w')
    o3plot.plot_two_d_system(tds, win, c2='w', cs='w')
    leg.addItem(pg.PlotDataItem([0], [0], pen='w'), name='2D system definition')
    for i in range(len(fc.sds)):
        win.plot(fc.sds[i][0], fc.sds[i][1], pen='y', symbol='o', symbolPen='y', symbolBrush='y', symbolSize=5, name='Important slope')
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
    o3plot.revamp_legend(leg)
    o3plot.show()
##%
fc.trim_grid_to_target_dh()
if show_trim_grid_to_target_dh:
    win = o3plot.create_scaled_window_for_tds(tds, title='trim_grid_to_target_dh')
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
    win = o3plot.create_scaled_window_for_tds(tds, title='build_req_y_node_positions')
    o3plot.plot_two_d_system(tds, win)
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
    win = o3plot.create_scaled_window_for_tds(tds, title='build_y_coords_at_xcs')
    o3plot.plot_two_d_system(tds, win)
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
if show_set_x_nodes:
    win = o3plot.create_scaled_window_for_tds(tds, title='set_x_nodes')
    o3plot.plot_two_d_system(tds, win)
    for i in range(len(fc.x_nodes)):
        win.addItem(pg.InfiniteLine(fc.x_nodes[i], angle=90, pen='r'))
    for i in range(len(fc.xcs_sorted)):
        win.addItem(pg.InfiniteLine(fc.xcs_sorted[i], angle=90, pen=(0, 255, 0, 100)))

    o3plot.show()


##%
fc.build_y_coords_grid_via_propagation()
if show_build_y_coords_grid_via_propagation:
    win = o3plot.create_scaled_window_for_tds(tds, title='build_y_coords_grid_via_propagation')
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
if show_set_to_decimal_places:
    win = o3plot.create_scaled_window_for_tds(tds, title='set_to_decimal_places')
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
fc.adjust_for_smooth_surface()
if show_smooth_surf:
    if show_build_y_coords_grid_via_propagation:
        win = o3plot.create_scaled_window_for_tds(tds, title='build_y_coords_grid_via_propagation')
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
fc.set_soil_ids_to_vary_xy_grid()
inds = np.where(fc.soil_grid == fc._inactive_value)
fc.soil_grid[inds] = 10
fc.create_mesh()
if show_set_soil_ids_to_grid:
    win = o3plot.create_scaled_window_for_tds(tds, title='set_soil_ids_to_grid')
    o3plot.plot_finite_element_mesh_onto_win(win, fc.femesh)
    win.plot(tds.x_surf, tds.y_surf)
    o3plot.show()

##%
fc.exclude_fd_eles()
if show_exclude_fd_eles:
    win = o3plot.create_scaled_window_for_tds(tds, title='exclude_fd_eles')
    o3plot.plot_finite_element_mesh_onto_win(win, fc.femesh)
    o3plot.show()