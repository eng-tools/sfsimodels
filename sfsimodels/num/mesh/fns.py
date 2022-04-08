import numpy as np
from ...num import mesh


def remove_close_items(y, tol, del_prev=True):
    diffs = np.diff(y)
    pairs = []
    inds = np.where(diffs < tol)
    while len(inds[0]):  # progressively delete coordinate below until tolerance is reached
        pairs.append((y[inds[0][0]], y[inds[0][0] + 1]))
        if del_prev:
            y = np.delete(y, inds[0][0])
        else:
            y = np.delete(y, inds[0][0] + 1)

        diffs = np.diff(y)
        inds = np.where(diffs < tol)
    return y, pairs


def build_ele2_node_array(femesh):
    x_all = femesh.x_nodes
    y_all = femesh.y_nodes
    x_inds = []
    y_inds = []
    if hasattr(y_all[0], '__len__'):  # can either have varying y-coordinates or single set
        n_y = len(y_all[0])
    else:
        n_y = 0

    ele_nums = np.cumsum(np.where(femesh.soil_grid != femesh.inactive_value + 1, 1, 0).flatten()) - 1

    for xx in range(len(femesh.soil_grid)):
        x_ele = [xx, xx + 1, xx + 1, xx]
        x_inds += [x_ele for i in range(n_y - 1)]
        for yy in range(len(femesh.soil_grid[xx])):
            y_ele = [yy + xx, yy + (xx + 1), yy + 1 + (xx + 1), yy + 1 + xx]
            y_inds.append(y_ele)
    xs = np.array(x_inds)
    ys = np.array(y_inds)
    node_nums = ys + xs * (len(femesh.soil_grid[0])) + 1
    ele2nodes = dict(zip(ele_nums, node_nums))

    return ele2nodes


def load_femesh(ffp, ecp_models, x_nodes2d, prefix='', suffix=''):
    x_nodes = np.loadtxt(ffp + f'{prefix}x_nodes{suffix}.txt')
    y_nodes = np.loadtxt(ffp + f'{prefix}y_nodes{suffix}.txt')
    soil_grid = np.loadtxt(ffp + f'{prefix}soil_grid{suffix}.txt', dtype=int)
    soils_list = np.loadtxt(ffp + f'{prefix}soils{suffix}.txt', dtype=str)
    if soils_list.size == 1:
        soils_list = [np.asscalar(soils_list)]
    soils = []
    for soil_hash in soils_list:
        sl_obj = None
        for sl_id in ecp_models['soil']:
            sl = ecp_models['soil'][sl_id]
            if sl.loaded_unique_hash == soil_hash:
                sl_obj = sl
                break
        soils.append(sl_obj)

    if x_nodes2d is not None:
        return mesh.FiniteElementVaryXY2DMesh(x_nodes, y_nodes, soil_grid, soils)
    else:
        return mesh.FiniteElementVaryY2DMesh(x_nodes, y_nodes, soil_grid, soils)


def save_femesh(ffp, femesh, prefix='', suffix=''):
    np.savetxt(ffp + f'{prefix}x_nodes{suffix}.txt', femesh.x_nodes, fmt='%.4g')
    np.savetxt(ffp + f'{prefix}y_nodes{suffix}.txt', femesh.y_nodes, fmt='%.4g')
    np.savetxt(ffp + f'{prefix}soil_grid{suffix}.txt', femesh.soil_grid, fmt='%i')
    with open(ffp + f'{prefix}soils{suffix}.txt', 'w') as ofile:
        ofile.write('\n'.join([sl.unique_hash for sl in femesh.soils]))


def get_nearest_xy_ind(xs, ys, x_point, y_point):
    distance = (ys - y_point) ** 2 + (xs - x_point) ** 2
    return np.where(distance == distance.min())[0]
