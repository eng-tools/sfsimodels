import numpy as np

from sfsimodels.models.systems import TwoDSystem
from sfsimodels.functions import interp_left


class FiniteElement2DMesh(object):
    x_act = None
    y_flat = None
    x_nodes = None
    y_nodes = None
    soils = None
    profile_indys = None

    def __init__(self, tds, dy_target, x_scale_pos, x_scale_vals, dp: int=None):
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
        """
        assert isinstance(tds, TwoDSystem)
        self.tds = tds
        self.dy_target = dy_target
        self.x_scale_pos = x_scale_pos
        self.x_scale_vals = x_scale_vals
        self.dp = dp
        self.xs = list(self.tds.x_sps)
        
        self.xs.append(tds.width)
    
        self.y_surf_at_sps = np.interp(self.xs, tds.x_surf, tds.y_surf)
        self.get_actual_lims()
        self.set_y_nodes()
        self.set_x_nodes()
        if self.dp is not None:
            self.set_to_decimal_places()
        self.set_soil_ids_to_grid()
    
    def get_actual_lims(self):
        """Find the x and y coordinates that should be maintained in the FE mesh"""
        x_act = [0]
        y_flat = []
        for i in range(len(self.tds.sps)):
            int_yy = [self.tds.sps[i].layer_depth(yy) for yy in range(1, self.tds.sps[i].n_layers + 1)]
            int_yy.append(self.tds.sps[i].height)
            
            # generate x_curr which stores important x-coordinates that are between two soil profiles
            inds = np.where((self.tds.x_surf < self.xs[i + 1]) & (self.tds.x_surf >= self.xs[i]))
            x_curr = self.tds.x_surf[inds]
            if self.xs[i] not in x_curr:
                x_curr = np.insert(x_curr, 0, self.xs[i])
            if self.xs[i + 1] not in x_curr:
                x_curr = np.insert(x_curr, len(x_curr), self.xs[i + 1])

            # Surface
            y_curr_surf = np.interp(x_curr, self.tds.x_surf, self.tds.y_surf)  # array of y-pos at important x for each layer
            x_diffs = x_curr - x_curr[0]
            x_act += list(x_curr[1:])
            
            x_temp = list(x_curr)  # UNUSED
            if i != 0:
                x_temp[0] += 1.0e-14

            for x in range(len(x_curr)):
                y_flat.append(y_curr_surf[x])
            for yy in range(len(int_yy) - 1):
                y1_curr = self.y_surf_at_sps[i] - int_yy[yy + 1]
                y_curr = y1_curr + self.tds.sps[i].x_angles[yy] * x_diffs
                y_curr = np.clip(y_curr, -self.tds.height, None)
                y_flat += list(y_curr)
        self.x_act = x_act
        self.y_flat = y_flat

    def set_y_nodes(self):
        """Determine the optimal position of node y-coordinates"""
        y_flat = np.array(list(set(self.y_flat)))
        min_y = -1e10
        layers = []
        while min_y < max(self.tds.y_surf):
            min_y = min(y_flat)
            inds = np.where(y_flat < min_y + self.dy_target)
            layer = np.mean(y_flat[inds])
            y_flat[inds] = 1000
            layers.append(layer)
        dys = [0]
        for i in range(1, len(layers)):
            dy_lay = layers[i] - layers[i - 1]
            approx_n_eles = dy_lay / self.dy_target
            n_eles = int(approx_n_eles + 0.99)
            dy_ele = dy_lay / n_eles
            dys += ([dy_ele] * n_eles)
        self.y_nodes = max(self.tds.y_surf) - np.cumsum(dys)

    def set_x_nodes(self):
        """Determine optimal position of node x-coordinates"""
        dxs = [0]
        for xx in range(1, len(self.x_act)):
            x_shift = self.x_act[xx] - self.x_act[xx - 1]
            x_incs = np.linspace(self.x_act[xx - 1], self.x_act[xx], 20)
            scale = interp_left(x_incs, self.x_scale_pos, self.x_scale_vals)
            av_scale = np.mean(scale)
            av_size = av_scale * self.dy_target
            n_x_eles = int(x_shift / av_size + 0.99)
            x_start = self.x_act[xx - 1]
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
    
        self.x_nodes = np.cumsum(dxs)

    def set_to_decimal_places(self):
        """Adjusts the node coordinates to a certain number of decimal places"""
        self.y_nodes = np.round(self.y_nodes, self.dp)
        self.x_nodes = np.round(self.x_nodes, self.dp)

    def set_soil_ids_to_grid(self):
        # Assign soil to element grid
        x_centres = (self.x_nodes[:-1] + self.x_nodes[1:]) / 2
        y_centres = (self.y_nodes[:-1] + self.y_nodes[1:]) / 2
        surf_centres = np.interp(x_centres, self.tds.x_surf, self.tds.y_surf)
        self.soils = np.zeros((len(x_centres), len(y_centres)), dtype=int)
        self.profile_indys = interp_left(x_centres, self.tds.x_sps, np.arange(0, len(self.tds.x_sps)))
        self.profile_indys = np.array(self.profile_indys, dtype=int)
        for xx in range(len(self.soils)):
            for yy in range(len(self.soils[0])):
                pid = self.profile_indys[xx]
                sp = self.tds.sps[pid]
                if y_centres[yy] > surf_centres[xx]:
                    self.soils[xx][yy] = -1
                    continue
                x_angles = [10] + list(sp.x_angles)
                sp_x = self.tds.x_sps[pid]
                for ll in range(1, sp.n_layers + 1):
                    if -y_centres[yy] > (sp.layer_depth(ll) - x_angles[ll - 1] * (x_centres[xx] - sp_x) - self.y_surf_at_sps[pid]):
                        pass
                    else:
                        self.soils[xx][yy] = ll - 1
                        break
                    if ll == sp.n_layers:
                        self.soils[xx][yy] = ll

    def get_indexes_at_depths(self, depths):
        return len(self.y_nodes) - (interp_left(depths, self.y_nodes[::-1]) + 1) - 1

    def get_indexes_at_xs(self, xs):
        return interp_left(xs, self.x_nodes)


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
    sp.x_angles = [0.0, 0.05, 0.0]
    sp2.x_angles = [0.0, 0.00, 0.0]

    fd = sm.RaftFoundation()
    fd.width = 2
    fd.depth = 0
    fd.length = 100
    tds = TwoDSystem()
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
    femesh = FiniteElement2DMesh(tds, 0.3, x_scale_pos=x_scale_pos, x_scale_vals=x_scale_vals)


if __name__ == '__main__':
    # plot2()
    _example_run()
    # replot()
