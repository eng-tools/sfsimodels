import numpy as np

from sfsimodels.models.systems import TwoDSystem
from sfsimodels.functions import interp_left
from .fns import remove_close_items


class FiniteElementOrth2DMesh(object):
    def __init__(self, x_nodes=None, y_nodes=None, soil_grid=None, soils=None, inactive_value=1e6):
        self.x_nodes = x_nodes
        self.y_nodes = y_nodes
        self.soil_grid = soil_grid
        self._soils = soils
        self.inactive_value = inactive_value

    def get_active_nodes(self):
        # Pad soil_grid with inactive values around edge
        sg_w_pad = self.inactive_value * np.ones((len(self.soil_grid) + 2, len(self.soil_grid[0]) + 2))
        sg_w_pad[1:-1, 1:-1] = self.soil_grid
        # Then compute the average soil_grid from four elements
        node_grid = (sg_w_pad[:-1, :-1] + sg_w_pad[:-1, 1:] + sg_w_pad[1:, :-1] + sg_w_pad[1:, 1:]) / 4
        # if average is equal to inactive then node is not active
        return np.where(node_grid == self.inactive_value, 0, 1)

    @property
    def soils(self):
        return self._soils

    @soils.setter
    def soils(self, sls):
        self._soils = sls

    @property
    def x_nodes(self):
        return self._x_nodes

    @x_nodes.setter
    def x_nodes(self, x_nodes):
        if isinstance(x_nodes, str):
            self._x_nodes = np.loadtxt(x_nodes)
        else:
            self._x_nodes = x_nodes
        self.coords_mesh = None

    @property
    def y_nodes(self):
        return self._y_nodes

    @y_nodes.setter
    def y_nodes(self, y_nodes):
        if isinstance(y_nodes, str):
            self._y_nodes = np.loadtxt(y_nodes)
        else:
            self._y_nodes = y_nodes
        self.coords_mesh = None

    @property
    def soil_grid(self):
        return self._soil_grid

    @soil_grid.setter
    def soil_grid(self, soil_grid):
        if isinstance(soil_grid, str):
            self._soil_grid = np.loadtxt(soil_grid)
        else:
            self._soil_grid = soil_grid

    def get_indexes_at_depths(self, depths, low=None):
        return interp_left(-np.array(depths), -self.y_nodes, low=low)

    def get_indexes_at_xs(self, xs, low=None):
        return interp_left(xs, self.x_nodes, low=low)

    def get_nearest_node_index_at_x(self, x):
        return np.argmin(abs(self.x_nodes - x))

    @property
    def nny(self):
        return len(self.y_nodes)

    @property
    def nnx(self):
        return len(self.x_nodes)

    def set_to_decimal_places(self, dp):
        """Adjusts the node coordinates to a certain number of decimal places"""
        self.y_nodes = np.round(self.y_nodes, dp)
        self.x_nodes = np.round(self.x_nodes, dp)


class FiniteElementOrth2DMeshConstructor(object):
    x_act = None
    y_flat = None
    x_nodes = None
    y_nodes = None
    soils = None
    x_index_to_sp_index = None
    _inactive_value = 1000000

    def __init__(self, tds, dy_target, x_scale_pos=None, x_scale_vals=None, x_nodes=None, dp: int = None, rm_fd_eles=0, fd_eles=0, x_sym=0):
        """
        A finite element mesh of a two-dimension system

        Parameters
        ----------
        tds: TwoDSystem
            A two dimensional system of models
        dy_target: float
            Target height of elements
        x_scale_pos: array_like
            x-positions used to provide scale factors for element widths
        x_scale_vals: array_like
            scale factors for element widths
        dp: int
            Number of decimal places
        rm_fd_eles: int
            If true then set foundation elements to inactive
        fd_eles: int
            If true then set foundation elements to inactive (deprecated)
        x_sym: int
            If true then mesh should be symmetric around the centre along x-axis
        """
        assert isinstance(tds, TwoDSystem)
        self.tds = tds
        self.dy_target = dy_target
        if x_scale_pos is None:
            x_scale_pos = [0, tds.width]
        if x_scale_vals is None:
            x_scale_vals = [1., 1.]
        self.x_scale_pos = np.array(x_scale_pos)
        self.x_scale_vals = np.array(x_scale_vals)
        self.dp = dp
        self.xs = list(self.tds.x_sps)
        self.x_sym = x_sym

        self.xs.append(tds.width)
        self.xs = np.array(self.xs)

        self.y_surf_at_sps = np.interp(self.xs, tds.x_surf, tds.y_surf)
        self._soils = []
        self._soil_hashes = []
        for i in range(len(self.tds.sps)):
            for yy in range(1, self.tds.sps[i].n_layers + 1):
                sl = self.tds.sps[i].layer(yy)
                if sl.unique_hash not in self._soil_hashes:
                    self._soil_hashes.append(sl.unique_hash)
                    self._soils.append(sl)
        self.get_actual_lims()
        self.set_y_nodes()
        if x_nodes is not None:
            self.x_nodes = x_nodes
        else:
            self.set_x_nodes()
        if self.dp is not None:
            self.set_to_decimal_places()
        self.set_soil_ids_to_grid()
        self.create_mesh()
        if not (fd_eles + rm_fd_eles):
            self.exclude_fd_eles()
        self._active_nodes = None


    def get_actual_lims(self):
        """Find the x and y coordinates that should be maintained in the FE mesh"""
        x_act = [0]
        y_flat = []
        fd_coords = []
        for i in range(len(self.tds.bds)):
            x_bd = self.tds.x_bds[i]
            bd = self.tds.bds[i]
            lip = getattr(bd.fd, bd.fd.ip_axis)
            fd_centre_x = x_bd + bd.x_fd
            if lip > self.dy_target:
                fd_coords.append(fd_centre_x)
            fd_coords.append(fd_centre_x - lip / 2)
            fd_coords.append(fd_centre_x + lip / 2)
        fd_coords = np.array(fd_coords)
        for i in range(len(self.tds.sps)):
            int_yy = [self.tds.sps[i].layer_depth(yy) for yy in range(1, self.tds.sps[i].n_layers + 1)]
            int_yy.append(self.tds.sps[i].height)

            # generate x_curr which stores important x-coordinates that are between two soil profiles
            inds = np.where((self.tds.x_surf < self.xs[i + 1]) & (self.tds.x_surf >= self.xs[i]))
            x_sf_curr = self.tds.x_surf[inds]
            fd_inds = np.where((fd_coords < self.xs[i + 1]) & (fd_coords >= self.xs[i]))
            x_fd_curr = fd_coords[fd_inds]
            x_curr = np.concatenate([x_sf_curr, x_fd_curr])
            x_curr.sort()

            if self.xs[i] not in x_curr:
                x_curr = np.insert(x_curr, 0, self.xs[i])
            if self.xs[i + 1] not in x_curr:
                x_curr = np.insert(x_curr, len(x_curr), self.xs[i + 1])

            for bb in range(len(self.tds.bds)):
                x_bd = self.tds.x_bds[bb]
                bd = self.tds.bds[bb]
                fd = bd.fd
                x_lhs = x_bd + bd.x_fd - fd.width / 2
                x_rhs = x_bd + bd.x_fd + fd.width / 2
                y_base_foundation = np.interp(x_bd + bd.x_fd, self.tds.x_surf, self.tds.y_surf) - fd.depth
                if self.xs[i] < x_lhs < self.xs[i + 1]:
                    y_flat.append(y_base_foundation)
                elif self.xs[i] < x_rhs < self.xs[i + 1]:
                    y_flat.append(y_base_foundation)

            # Surface
            y_curr_surf = np.interp(x_curr, self.tds.x_surf, self.tds.y_surf)  # array of y-pos at important x for each layer
            x_diffs = x_curr - x_curr[0]
            x_act += list(x_curr[1:])

            x_temp = list(x_curr)  # UNUSED
            if i != 0:
                x_temp[0] += 1.0e-14

            for x in range(len(x_curr)):
                if y_curr_surf[x] not in y_flat:
                    y_flat.append(y_curr_surf[x])
            for yy in range(len(int_yy) - 1):
                y1_curr = self.y_surf_at_sps[i] - int_yy[yy + 1]
                y_curr = y1_curr + self.tds.sps[i].x_angles[yy] * x_diffs
                y_curr = np.clip(y_curr, -self.tds.height, None)
                y_flat += list(y_curr)
        x_act.sort()
        x_act, pairs = remove_close_items(x_act, self.dy_target * 0.25, del_prev=False)
        # x_diff = np.diff(x_act)

        self.x_act = x_act
        self.y_flat = y_flat

    def set_y_nodes(self):
        """Determine the optimal position of node y-coordinates"""
        y_flat = np.array(list(set(self.y_flat)))
        min_y = -1e10
        layers = []  # builds from lowest first
        while min_y < max(self.tds.y_surf):
            min_y = min(y_flat)
            inds = np.where(y_flat < min_y + self.dy_target * 0.25)
            layer = np.mean(y_flat[inds])
            y_flat[inds] = 1000
            layers.append(layer)
        dys = []
        for i in range(1, len(layers)):
            dy_lay = layers[i] - layers[i - 1]
            approx_n_eles = dy_lay / self.dy_target
            n_eles = int(approx_n_eles + 0.99)
            dy_ele = dy_lay / n_eles
            dys += ([dy_ele] * n_eles)
        dys.append(0)
        self.y_nodes = max(self.tds.y_surf) - np.cumsum(dys[::-1])

    def set_x_nodes(self):
        """Determine optimal position of node x-coordinates"""
        dxs = [0]
        symmetric = self.x_sym
        if not symmetric:
            x_targets = self.x_act
        else:
            x_targets = np.array(list(self.x_act))
            x_ref = self.tds.width / 2
            ind = np.argmin(abs(x_targets - x_ref))
            if (x_targets[ind] - x_ref) / self.dy_target < 0.5:
                x_targets[ind] = x_ref
                x_targets = x_targets[:ind+1]
            else:
                if x_targets[ind] > x_ref:
                    x_targets[ind] = x_ref
                    x_targets = x_targets[:ind+1]
                else:
                    x_targets[ind + 1] = x_ref
                    x_targets = x_targets[:ind+2]
        for xx in range(1, len(x_targets)):
            x_shift = x_targets[xx] - x_targets[xx - 1]
            x_incs = np.linspace(x_targets[xx - 1], x_targets[xx], 20)
            scale = interp_left(x_incs, self.x_scale_pos, self.x_scale_vals)
            av_scale = np.mean(scale)
            av_size = av_scale * self.dy_target
            n_x_eles = int(x_shift / av_size + 0.99)
            x_start = x_targets[xx - 1]
            x_incs = []
            for n in range(n_x_eles):
                prox_x_inc = interp_left([x_start], self.x_scale_pos, self.x_scale_vals)[0] * self.dy_target
                x_temp_points = np.linspace(x_start, x_start + prox_x_inc, 5)
                curr_scale = np.mean(interp_left(x_temp_points, self.x_scale_pos, self.x_scale_vals))
                x_inc = curr_scale * self.dy_target
                x_incs.append(x_inc)
                x_start += x_inc
            x_incs = np.array(x_incs) * x_shift / sum(x_incs)
            dxs += list(x_incs)
        if symmetric:
            dxs = dxs + dxs[1:][::-1]
        x_nodes = np.cumsum(dxs)

        # if not symmetric:
        self.x_nodes = x_nodes
        # else:
        #     x_ref = self.tds.width / 2
        #     ind = np.argmin(abs(x_nodes - x_ref))
        #     if x_nodes[ind] >= x_ref:
        #         ind -= 1
        #     rat = (x_ref - x_nodes[ind]) / (x_nodes[ind + 1] - x_nodes[ind])
        #     node_at_centre = True
        #     if rat > 0.8:  # use ind + 1 as reflection
        #         x_lhs = x_nodes[:ind + 1]
        #         x_rhs = x_nodes[ind + 2:]
        #     elif rat < 0.2: # use ind as reflection
        #         x_lhs = x_nodes[:ind]
        #         x_rhs = x_nodes[ind + 1:]
        #     else:  # consider no node at centre point
        #         x_lhs = x_nodes[:ind]
        #         x_rhs = x_nodes[ind:]
        #         node_at_centre = False
        #     x_rhs_eq = (self.tds.width - x_rhs)[::-1]
        #     # if len(x_rhs_eq) > len(x_lhs)
        #     x_side = (x_lhs + x_rhs_eq) / 2
        #     if node_at_centre:
        #         x_nodes = np.array(list(x_side) + [x_ref] + list((self.tds.width - x_side)[::-1]))
        #     else:
        #         x_nodes = np.array(list(x_side) + list((self.tds.width - x_side)[::-1]))
        #     self.x_nodes = x_nodes

    def set_to_decimal_places(self):
        """Adjusts the node coordinates to a certain number of decimal places"""
        self.y_nodes = np.round(self.y_nodes, self.dp)
        self.x_nodes = np.round(self.x_nodes, self.dp)

    def set_soil_ids_to_grid(self):
        # Assign soil to element grid
        x_centres = (self.x_nodes[:-1] + self.x_nodes[1:]) / 2
        y_centres = (self.y_nodes[:-1] + self.y_nodes[1:]) / 2
        surf_centres = np.interp(x_centres, self.tds.x_surf, self.tds.y_surf)
        self.soil_grid = np.zeros((len(x_centres), len(y_centres)), dtype=int)
        self.x_index_to_sp_index = interp_left(x_centres, self.tds.x_sps, np.arange(0, len(self.tds.x_sps)))
        self.x_index_to_sp_index = np.array(self.x_index_to_sp_index, dtype=int)
        for xx in range(len(self.soil_grid)):
            for yy in range(len(self.soil_grid[0])):
                pid = self.x_index_to_sp_index[xx]
                sp = self.tds.sps[pid]
                if y_centres[yy] > surf_centres[xx]:
                    self.soil_grid[xx][yy] = self._inactive_value
                    continue
                x_angles = [10] + list(sp.x_angles)
                sp_x = self.tds.x_sps[pid]
                for ll in range(1, sp.n_layers + 1):
                    if -y_centres[yy] > (
                            sp.layer_depth(ll) - x_angles[ll - 1] * (x_centres[xx] - sp_x) - self.y_surf_at_sps[pid]):
                        pass
                    else:
                        unique_hash = sp.layer(ll - 1).unique_hash
                        self.soil_grid[xx][yy] = self._soil_hashes.index(unique_hash)
                        break
                    if ll == sp.n_layers:
                        unique_hash = sp.layer(ll).unique_hash
                        self.soil_grid[xx][yy] = self._soil_hashes.index(unique_hash)
                        break

    def get_active_nodes(self):
        # active_nodes = np.ones((len(self.x_nodes), len(self.y_nodes)), dtype=int)  # Start with all active
        # Pad soil_grid with inactive values around edge
        sg_w_pad = self._inactive_value * np.ones((len(self.soil_grid) + 2, len(self.soil_grid[0]) + 2))
        sg_w_pad[1:-1, 1:-1] = self.soil_grid
        # Then compute the average soil_grid from four elements
        node_grid = (sg_w_pad[:-1, :-1] + sg_w_pad[:-1, 1:] + sg_w_pad[1:, :-1] + sg_w_pad[1:, 1:]) / 4
        # if average is equal to inactive then node is not active
        # inds = np.where(node_grid == self._inactive_value)
        return np.where(node_grid == self._inactive_value, 0, 1)

    @property
    def inactive_value(self):
        return self._inactive_value

    @inactive_value.setter
    def inactive_value(self, value):
        self._inactive_value = value

    
    @property
    def active_nodes(self):
        if self._active_nodes is None:
            self._active_nodes = self.get_active_nodes()
        return self._active_nodes

    @property
    def soils(self):
        return self._soils

    def get_indexes_at_depths(self, depths, low=None):
        return interp_left(-np.array(depths), -self.y_nodes, low=low)

    def get_indexes_at_xs(self, xs, low=None):
        return interp_left(xs, self.x_nodes, low=low)

    def get_nearest_node_index_at_x(self, x):
        return np.argmin(abs(self.x_nodes - x))

    @property
    def nny(self):
        return len(self.y_nodes)

    @property
    def nnx(self):
        return len(self.x_nodes)

    def create_mesh(self):
        self.femesh = FiniteElementOrth2DMesh(self.x_nodes, self.y_nodes, self.soil_grid, self.soils)

    def exclude_fd_eles(self):
        for i, bd in enumerate(self.tds.bds):
            fd = bd.fd
            fcx = self.tds.x_bds[i] + bd.x_fd
            fcy = np.interp(fcx, self.tds.x_surf, self.tds.y_surf)
            lip = getattr(bd.fd, bd.fd.ip_axis)
            xs = np.array([fcx - lip / 2, fcx + lip / 2])
            ys = np.array([fcy - fd.depth, fcy - fd.depth + fd.height])
            xsi = self.get_nearest_node_index_at_x(xs[0])
            xei = self.get_nearest_node_index_at_x(xs[1])
            # xsi, xei = self.get_indexes_at_xs(xs)
            yei, ysi = self.get_indexes_at_depths(ys, low='min')
            # create foundation nodes a soil mesh nodes
            # along the base
            j = 0
            for xx in range(xsi, xei):
                for yy in range(ysi, yei):
                    self.soil_grid[xx][yy] = self._inactive_value
                    self.femesh.soil_grid[xx][yy] = self.femesh.inactive_value


def construct_femesh_orth(tds, dy_target, x_scale_pos=None, x_scale_vals=None, x_sym=0, rm_fd_eles=0):
    fc = FiniteElementOrth2DMeshConstructor(tds, dy_target, x_scale_pos=x_scale_pos, x_scale_vals=x_scale_vals,
                                            x_sym=x_sym, rm_fd_eles=rm_fd_eles)
    femesh = fc.femesh
    assert isinstance(femesh, FiniteElementOrth2DMesh)
    return femesh


def _example_run():
    vs = 150.0
    rho = 1.8
    g_mod = vs ** 2 * rho
    import sfsimodels as sm
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
    sp.x_angles = [0.05, 0.0, 0.0]
    sp2.x_angles = [0.0, 0.00, 0.0]

    fd = sm.RaftFoundation()
    fd.width = 2
    fd.depth = 0
    fd.length = 100
    fd.ip_axis = 'width'
    tds = TwoDSystem(width=40, height=15)
    tds.add_sp(sp, x=0)
    tds.add_sp(sp2, x=14)
    tds.x_surf = np.array([0, 10, 12, 40])
    tds.y_surf = np.array([0, 0, 2, 2])
    bd = sm.NullBuilding()
    bd.set_foundation(fd, x=0.0)
    tds.add_bd(bd, x=8)

    x_scale_pos = np.array([0, 5, 15, 30])
    x_scale_vals = np.array([2., 1.0, 2.0, 3.0])
    fc = FiniteElementOrth2DMeshConstructor(tds, 0.3, x_scale_pos=x_scale_pos, x_scale_vals=x_scale_vals)
    femesh = fc.femesh


if __name__ == '__main__':
    # plot2()
    _example_run()
    # replot()

