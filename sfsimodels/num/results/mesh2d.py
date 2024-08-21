import numpy as np

from sfsimodels.num.mesh.fns import calc_quad_centroids


class Results2D(object):
    coords = None
    time = None
    x_disp = None
    y_disp = None
    node_c = None
    ele_c = None
    selected_nodes = None
    used_r_starter = 0
    mat2ele_tags = None  # Assume 1-to-1 so if it uses a section then should be null
    sect2ele_tags = None  # Store position and tag - UNUSED
    mat2sect_tags = None  # UNUSED  # TODO: implement
    n_nodes_per_ele = [2, 4, 8]  # for 2D
    ele_num_base = 1
    selected_nodes = None
    _selected_node_tags = None

    def __init__(self, coords, x_disp, y_disp, time=None):
        self.coords = coords
        self.x_disp = x_disp
        self.y_disp = y_disp
        self.time = time
        self.ele2node_tags = {}
        self.meta_files = ['node_c', 'ele_c', 'mat2ele_tags', 'sect2ele_tags', 'mat2sect_tags']
        self.meta_fmt = [None, '%i', '%i', '%i']
        self.pseudo_dt = None  # use if recording steps of a static analysis


    @property
    def selected_node_tags(self):
        if self._selected_node_tags is None:
            if self.selected_nodes is None:
                return None
            self._selected_node_tags = [x.tag for x in self.selected_nodes]
        return self._selected_node_tags

    @selected_node_tags.setter
    def selected_node_tags(self, tags):
        self._selected_node_tags = tags

    @property
    def dt(self):
        if self._dt is None:
            if self.time is not None:
                self._dt = (self.time[-1] - self.time[0]) / (len(self.time) - 1)
        return self._dt

    @dt.setter
    def dt(self, dt):
        self._dt = dt

    def rezero_node_tags(self, osi=None):
        from numpy import arange, searchsorted, where
        node_tags = self.selected_node_tags
        new_node_tags = arange(1, len(node_tags) + 1)
        sidx = node_tags.argsort()
        k = node_tags[sidx]
        v = new_node_tags[sidx]
        for ele_tag in self.ele2node_tags:
            curr_tags = self.ele2node_tags[ele_tag]
            idx = searchsorted(k, curr_tags)
            assert max(idx) < len(k)
            mask = k[idx] == curr_tags
            self.ele2node_tags[ele_tag] = where(mask, v[idx], len(k))

    def get_eles_by_n_nodes(self, n_nodes):
        eles_by_n_nodes = {2: [], 4: [], 8: []}
        for ele in self.ele2node_tags:
            nn = len(self.ele2node_tags[ele])
            eles_by_n_nodes[nn].append(ele)
        return eles_by_n_nodes[n_nodes]

    def compute_ele_strains_and_disps(self):  # currently only available for quad elements
        import numpy as np
        rd = {}
        eles = self.get_eles_by_n_nodes(4)
        nodes = np.array([self.ele2node_tags[ele] for ele in eles]) - 1
        xd = self.x_disp[:, nodes].transpose(1, 2, 0)
        yd = self.y_disp[:, nodes].transpose(1, 2, 0)
        xc = self.coords[nodes, 0]
        yc = self.coords[nodes, 1]
        x_disp_ele, y_disp_ele = calc_quad_centroids(xc[:, :, np.newaxis] + xd, yc[:, :, np.newaxis] + yd, axis=-2)

        rd['XDISP'] = x_disp_ele - x_disp_ele[:, 0][:, np.newaxis]
        rd['YDISP'] = y_disp_ele - y_disp_ele[:, 0][:, np.newaxis]

        # return
        # nodes must be anti-clockwise
        xc0 = xc[0]
        yc0 = yc[0]
        i = 0
        for i in range(4):
            if xc0[i%4] < xc0[(i+1)%4] and xc0[(i+2)%4] > xc0[(i+3)%4] and yc0[(i+1)%4] < yc0[(i+2)%4]:  # i=bottom-left
                break
            if i == 3:
                print('WARNING could not find bottom left')
        inds = np.roll(np.arange(4), i)
        xc = xc[:, inds]
        yc = yc[:, inds]
        xd = xd[:, inds]
        yd = yd[:, inds]

        xlen = (xc[:, 1] - xc[:, 0] + xc[:, 2] - xc[:, 3]) / 2
        xdelta = (xd[:, 1] - xd[:, 0] + xd[:, 2] - xd[:, 3]) / 2
        rd['EPS_XX'] = xdelta / xlen[:, np.newaxis]
        ylen = (yc[:, 2] - yc[:, 1] + yc[:, 3] - yc[:, 0]) / 2
        ydelta = (yd[:, 2] - yd[:, 1] + yd[:, 3] - yd[:, 0]) / 2
        rd['EPS_YY'] = ydelta / ylen[:, np.newaxis]

        xd_bot = (xd[:, 1] + xd[:, 0]) / 2
        xd_top = (xd[:, 2] + xd[:, 3]) / 2
        yd_lhs = (yd[:, 3] + yd[:, 0]) / 2
        yd_rhs = (yd[:, 2] + yd[:, 1]) / 2
        rd['EPS_XY'] = ((xd_bot - xd_top) / ylen[:, np.newaxis] + (yd_rhs - yd_lhs) / xlen[:, np.newaxis]) / 2  # +ve in anti-clockwise
        rd['SSTR_MAX'] = np.sqrt(((rd['EPS_XX'] - rd['EPS_YY']) / 2) ** 2 + rd['EPS_XY'] ** 2)
        rd['EPS_VOL'] = rd['EPS_XX'] + rd['EPS_YY']
        return rd


def build_ele2_node_array(femesh, ele_c=None):
    x_all = femesh.x_nodes
    y_all = femesh.y_nodes
    x_inds = []
    y_inds = []
    if hasattr(y_all[0], '__len__'):  # can either have varying y-coordinates or single set
        n_y = len(y_all[0])
    else:
        n_y = 0

    active_eles = np.where(femesh.soil_grid != femesh.inactive_value)
    is_active = np.where(femesh.soil_grid != femesh.inactive_value, 1, 0)
    ele_nums = np.cumsum(np.where(femesh.soil_grid != femesh.inactive_value + 1, 1, 0).flatten()) - 1

    # ele_nums = ele_nums.reshape(femesh.soil_grid.shape)

    for xx in range(len(femesh.soil_grid)):
        x_ele = [xx, xx + 1, xx + 1, xx]
        x_inds += [x_ele for i in range(n_y - 1)]
        # x_inds += x_ele * (n_y - 1)
        # y_inds.append([])
        for yy in range(len(femesh.soil_grid[xx])):
            y_ele = [yy + xx, yy + (xx + 1), yy + 1 + (xx + 1), yy + 1 + xx]
            y_inds.append(y_ele)
    xs = np.array(x_inds)
    ys = np.array(y_inds)
    node_nums = ys + xs * (len(femesh.soil_grid[0])) + 1
    ele2nodes = dict(zip(ele_nums, node_nums))

    return ele2nodes
