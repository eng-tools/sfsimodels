import numpy as np
from sfsimodels.models.abstract_models import PhysicalObject
from sfsimodels.models.systems import TwoDSystem
from sfsimodels.functions import interp_left, interp2d, interp3d
from .fns import remove_close_items, build_ele2_node_array
import hashlib


def sort_slopes(sds):
    """Sort slopes from bottom to top then right to left"""
    sds = np.array(sds)
    scores = sds[:, 0, 1] + sds[:, 1, 1] * 1e6
    inds = np.argsort(scores)
    return sds[inds]


def adjust_slope_points_for_removals(sds, x, removed_y, retained_y):
    for sd in sds:
        for i in range(2):
            if sd[0][i] == x and sd[1][i] == removed_y:
                sd[1][i] = retained_y


def adj_slope_by_layers(xm, ym, sgn=1):
    """
    Given mesh coordinates, adjust the mesh to be match the slope by adjust each layer

    bottom left and top right coords of mesh are the slope

    Parameters
    ----------
    xm
    ym
    x_slope - NOT needed
    y_slope

    Returns
    -------

    """
    # TODO use centroid formula - and use o3plot to get ele-coords
    ym = sgn * np.array(ym)
    xm = sgn * np.array(xm)

    if sgn == -1:
        xm = xm[::-1]
        ym = ym[::-1]
    nh = len(ym[0]) - 1
    # dy = min([(ym[0][-1] - ym[0][0]) / nh, (ym[-1][-1] - ym[-1][0]) / nh, 0.2])
    dy1 = min([(ym[-1][-1] - ym[-1][0]) / nh])
    dy0 = 0.2

    y0s = ym[0][0] + np.arange(nh + 1) * dy0
    y1s = ym[-1][-1] - np.arange(nh + 1) * dy1
    y1s = y1s[::-1]
    for i in range(nh + 1):
        ym[:, i] = np.interp(xm[:, i], [xm[0][0], xm[-1][-1]], [y0s[i], y1s[i]])
        xm[:, i] = xm[:, 0]
    y_centres_at_xns = (ym[1:] + ym[:-1]) / 2
    y_centres = (y_centres_at_xns[:, 1:] + y_centres_at_xns[:, :-1]) / 2
    # get x-coordinates of centres of relevant elements

    included_ele = []
    dy_inds = len(ym[0, :]) - 1
    for i in range(0, dy_inds):
        # account for shift before assessing position of centroid
        xcens = (xm[1:, i] + xm[:-1, i]) / 2 + 0.375 * (xm[1:, -1] - xm[:-1, -1])
        y_surf_at_x_cens = np.interp(xcens, [xm[0][0], xm[-1][-1]], [ym[0][0], ym[-1][-1]])
        inds = np.where(y_centres[:, i] < y_surf_at_x_cens)
        if len(inds[0]):
            included_ele.append(inds[0][0])
        else:
            included_ele.append(len(y_surf_at_x_cens))
    included_ele.append(len(y_surf_at_x_cens))
    new_xm = xm
    new_ym = ym
    for j in range(1, nh + 1):
        new_ym[included_ele[0], j] += dy1
    for i in range(1, dy_inds + 1):
        x_ind_adj = included_ele[i - 1]
        x_ind_adj_next = included_ele[i]
        if x_ind_adj == x_ind_adj_next:
            continue
        # shift by half of the ele
        dx = (xm[x_ind_adj + 1, i] - xm[x_ind_adj, i]) * 0.5
        dxs = np.interp(xm[x_ind_adj:x_ind_adj_next, i], [xm[x_ind_adj, i], xm[x_ind_adj_next, i]], [dx, 0])
        new_xm[x_ind_adj:x_ind_adj_next, i] = xm[x_ind_adj:x_ind_adj_next, i] + dxs
        for j in range(i + 1, nh + 1):
            new_ym[x_ind_adj_next, j] += dy1
    if sgn == -1:
        new_xm = new_xm[::-1]
        new_ym = new_ym[::-1]
    return new_xm * sgn, new_ym * sgn


def calc_centroid(xs, ys):
    import numpy as np
    x0 = np.array(xs)
    y0 = np.array(ys)
    x1 = np.roll(xs, 1, axis=-1)
    y1 = np.roll(ys, 1, axis=-1)
    a = x0 * y1 - x1 * y0
    xc = np.sum((x0 + x1) * a, axis=-1)
    yc = np.sum((y0 + y1) * a, axis=-1)

    area = 0.5 * np.sum(a, axis=-1)
    xc /= (6.0 * area)
    yc /= (6.0 * area)

    return xc, yc


def calc_mesh_centroids(fem):
    x_inds = []
    y_inds = []
    if hasattr(fem.y_nodes[0], '__len__'):  # can either have varying y-coordinates or single set
        n_y = len(fem.y_nodes[0])
    else:
        n_y = 0
    import numpy as np

    for xx in range(len(fem.soil_grid)):
        x_ele = [xx, xx + 1, xx + 1, xx]
        x_inds += [x_ele for i in range(n_y - 1)]
        for yy in range(len(fem.soil_grid[xx])):
            y_ele = [yy, yy, yy + 1, yy + 1]
            y_inds.append(y_ele)
    n_eles = len(np.array(x_inds))
    x_inds = np.array(x_inds).flatten()
    y_inds = np.array(y_inds).flatten()
    x0 = np.array(fem.x_nodes[x_inds, y_inds])
    y0 = np.array(fem.y_nodes[x_inds, y_inds])
    x0 = x0.reshape((n_eles, 4))
    y0 = y0.reshape((n_eles, 4))

    x1 = np.roll(x0, 1, axis=-1)
    y1 = np.roll(y0, 1, axis=-1)
    a = x0 * y1 - x1 * y0
    xc = np.sum((x0 + x1) * a, axis=-1)
    yc = np.sum((y0 + y1) * a, axis=-1)

    area = 0.5 * np.sum(a, axis=-1)
    xc /= (6.0 * area)
    yc /= (6.0 * area)

    return xc.reshape(len(fem.soil_grid), len(fem.soil_grid[0])), yc.reshape(len(fem.soil_grid), len(fem.soil_grid[0]))


class FiniteElementVary2DMeshConstructor(object):  # maybe FiniteElementVertLine2DMesh
    _soils = None
    x_index_to_sp_index = None
    _inactive_value = 1000000

    def __init__(self, tds, dy_target, x_scale_pos=None, x_scale_vals=None, dp: int = None, rm_fd_eles=0, fd_eles=0, auto_run=True,
                 use_3d_interp=False, smooth_surf=False, force_x2d=False, min_scale=0.5, max_scale=2.0,
                 allowable_slope=0.25, smooth_ratio=1.):
        """
        Builds a finite element mesh of a two-dimension system

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
            if =0 then elements corresponding to the foundation are removed, else provide element id
        fd_eles: int
            if =0 then elements corresponding to the foundation are removed, else provide element id (deprecated)
        smooth_surf: bool
            if true then changes in angle of the slope must be less than 90 degrees, builds VaryXY mesh
        """
        self.min_scale = min_scale
        self.max_scale = max_scale
        self.allowable_slope = allowable_slope
        self.smooth_ratio = smooth_ratio
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
        self.smooth_surf = smooth_surf

        self.xs.append(tds.width)
        self.xs = np.array(self.xs)
        inds = np.where(np.array(tds.x_surf) <= tds.width)
        self.x_surf = np.array(tds.x_surf)[inds]
        if tds.width not in self.x_surf:
            self.x_surf = np.insert(self.x_surf, len(self.x_surf), tds.width)
        self.y_surf = np.interp(self.x_surf, tds.x_surf, tds.y_surf)
        self.y_surf_at_sps = np.interp(self.xs, tds.x_surf, tds.y_surf)
        self._soils = []
        self._soil_hashes = []
        for i in range(len(self.tds.sps)):
            for yy in range(1, self.tds.sps[i].n_layers + 1):
                sl = self.tds.sps[i].layer(yy)
                if sl.unique_hash not in self._soil_hashes:
                    self._soil_hashes.append(sl.unique_hash)
                    self._soils.append(sl)

        self.y_surf_at_xcs = None
        self.yd = None
        self.xcs_sorted = None
        self.sds = None
        self.y_blocks = None
        self.y_coords_at_xcs = None
        self.x_nodes = None
        self.y_nodes = None
        self.x_nodes2d = None
        self._femesh = None

        if auto_run:
            self.get_special_coords_and_slopes()  # Step 1
            self.set_init_y_blocks()
            self.adjust_blocks_to_be_consistent_with_slopes()
            self.trim_grid_to_target_dh()
            self.build_req_y_node_positions()
            self.set_x_nodes()

            if use_3d_interp:
                self.build_y_coords_grid_via_3d_interp()
            else:
                self.build_y_coords_grid_via_propagation()
            if self.dp is not None:
                self.set_to_decimal_places()
            if smooth_surf:
                self.adjust_for_smooth_surface()
                self.set_soil_ids_to_vary_xy_grid()
            elif force_x2d:
                self.x_nodes2d = self.x_nodes[:, np.newaxis] * np.ones_like(self.y_nodes)
                self.set_soil_ids_to_vary_xy_grid()
            else:
                self.set_soil_ids_to_vary_y_grid()
            self.create_mesh()
            if smooth_surf:
                self.femesh.tidy_unused_mesh()
            if not (fd_eles + rm_fd_eles):
                self.exclude_fd_eles()

    def get_special_coords_and_slopes(self):
        """Find the coordinates, layer boundaries and surface slopes that should be maintained in the FE mesh"""
        fd_coords = []
        x_off = 0.0
        yd = {}
        for i in range(len(self.x_surf)):
            yd[self.x_surf[i]] = []
        if self.tds.width not in yd:
            yd[self.tds.width] = []

        sds = []  # slope dict (stored left-to-right and bottom-to-top)
        for i in range(len(self.tds.bds)):
            x_bd = self.tds.x_bds[i]
            bd = self.tds.bds[i]
            fd_centre_x = x_bd + bd.x_fd
            y_surf = np.interp(fd_centre_x, self.x_surf, self.y_surf)
            if bd.fd.width > self.dy_target:
                fd_coords.append(fd_centre_x)
            x_left = fd_centre_x - bd.fd.width / 2
            x_right = fd_centre_x + bd.fd.width / 2
            if x_left not in yd:
                yd[x_left] = []
            yd[x_left] += [y_surf, -bd.fd.depth + y_surf]
            if x_right not in yd:
                yd[x_right] = []
            yd[x_right] += [y_surf, -bd.fd.depth + y_surf]
            sds.append([[x_left, x_right], [y_surf, y_surf]])
            sds.append([[x_left, x_right], [-bd.fd.depth + y_surf, -bd.fd.depth + y_surf]])

        for i in range(len(self.tds.sps)):
            x_curr = self.tds.x_sps[i]
            if x_curr > self.tds.width:
                continue
            if i == len(self.tds.sps) - 1:
                x_next = self.tds.width
            else:
                x_next = self.tds.x_sps[i + 1] - x_off

            # get important x-coordinates that are between two soil profiles
            if x_curr not in yd:
                yd[x_curr] = []
            if x_next not in yd and x_next < self.tds.width:
                yd[x_next] = []
            x_coords = np.array(list(yd))
            inds = np.where((x_coords >= x_curr) & (x_coords <= x_next))
            xs = np.sort(x_coords[inds])
            y_surf_at_xs = np.interp(xs, self.x_surf, self.y_surf)
            y_curr_surf = y_surf_at_xs[0]
            # Depths from defined soil profile
            int_yy = []
            angles = []
            for yy in range(1, self.tds.sps[i].n_layers + 1):
                # if self.tds.sps[i].layer_depth(yy) >= 0:
                y = -self.tds.sps[i].layer_depth(yy) + y_curr_surf
                if -y < self.tds.height:
                    int_yy.append(y)
                    angles.append(self.tds.sps[i].x_angles[yy - 1])
            angles = np.array(angles)

            if xs[0] not in yd:
                yd[xs[0]] = []
            for j in range(len(xs) - 1):
                x0 = xs[j]
                x_next = xs[j + 1]
                if x_next not in yd:
                    yd[x_next] = []
                x0_diff = x0 - x_curr
                xn_diff = x_next - x_curr
                if y_surf_at_xs[j] not in yd[x0]:
                    yd[x0].append(y_surf_at_xs[j])
                if y_surf_at_xs[j + 1] not in yd[x_next]:
                    yd[x_next].append(y_surf_at_xs[j + 1])
                for k in range(len(int_yy)):
                    if angles[k] is None or np.isnan(angles[k]):
                        continue
                    y_curr = int_yy[k] + angles[k] * x0_diff
                    if y_curr < y_surf_at_xs[j] and y_curr not in yd[x0]:
                        yd[x0].append(y_curr)
                    y_next = int_yy[k] + angles[k] * xn_diff
                    if y_next < y_surf_at_xs[j + 1] and y_next not in yd[x_next]:
                        yd[x_next].append(y_next)
                    if y_curr <= y_surf_at_xs[j] and y_next <= y_surf_at_xs[j + 1]:
                        sds.append([[x0, x_next], [y_curr, y_next]])

        for x in yd:
            yd[x].append(-self.tds.height)
            yd[x].append(np.interp(x, self.x_surf, self.y_surf))
            yd[x] = list(set(yd[x]))
            yd[x].sort()
        xcs = list(yd)
        xcs.sort()
        xcs = np.array(xcs)
        for i in range(len(xcs) - 1):
            xs = np.array([xcs[i], xcs[i + 1]])
            slope = [list(xs), list(np.interp(xs, self.x_surf, self.y_surf))]
            if abs(slope[1][1] - slope[1][0]) / (slope[0][1] - slope[0][0]) > 0.8:
                continue
            if slope not in sds:
                sds.append(slope)
        y_surf_max = max(self.y_surf)

        # remove coordinates that are too close
        min_y = self.dy_target * self.min_scale
        tol = self.dy_target * self.min_scale
        for x in yd:
            yd[x], pairs = remove_close_items(yd[x], tol=tol)
            for pair in pairs:
                adjust_slope_points_for_removals(sds, x, pair[0], pair[1])

        self.y_surf_at_xcs = {}
        for x in yd:
            self.y_surf_at_xcs[x] = yd[x][-1]
            if y_surf_max not in yd[x] and abs(y_surf_max - max(yd[x])) > tol:
                yd[x] = np.insert(yd[x], len(yd[x]), y_surf_max)
            yd[x] = np.array(yd[x])
        self.yd = yd
        x_act = list(self.yd)
        x_act.sort()
        self.xcs_sorted = np.array(x_act)
        self.sds = sort_slopes(sds)

    def set_init_y_blocks(self):
        """For each significant vertical line, assign initial number of elements between each special y-coordinate"""
        xcs = self.xcs_sorted
        y_steps = []
        y_blocks = {}
        # Step 1: Define an initial set of y_node coordinates at each x-special-position
        h_target = self.dy_target
        yd_init_inds = []
        for i in range(len(xcs)):
            xc0 = xcs[i]
            y_blocks[xc0] = []
            y_steps.append([])
            yd_init_inds.append([0])

            for j in range(1, len(self.yd[xc0])):
                h_diff = -(self.yd[xc0][j - 1] - self.yd[xc0][j])
                n_blocks = int(np.round(h_diff / h_target))
                if n_blocks == 0:
                    n_blocks = 1
                y_blocks[xc0].append(n_blocks)

        n_blocks = [sum(y_blocks[xcs]) for xcs in y_blocks]
        n_max = max(n_blocks)
        # Step 2: make sure that each column has same number of temp y positions
        #  - first check if n_blocks less than maximum,
        #  - if less then add extra elements to the largest thickness
        for i in range(len(xcs)):
            xc0 = xcs[i]
            if len(y_steps[i]) < n_max:
                n_extra = n_max - n_blocks[i]  # number of blocks to add
                h_diffs = np.diff(self.yd[xc0])  # thickness of each zone
                for nn in range(n_extra):
                    dh_options = h_diffs / (np.array(y_blocks[xc0]) + 1)
                    # index of the zone with thickest average element, where new element will be added
                    ind_max = np.argmax(dh_options)
                    y_blocks[xc0][ind_max] += 1
        self.y_blocks = y_blocks

    def adjust_blocks_to_be_consistent_with_slopes(self):
        """Change the number of elements between special y-coords to try to maintain defined slopes"""
        min_dh = self.min_scale * self.dy_target
        max_dh = self.max_scale * self.dy_target
        xcs = list(self.yd)
        xcs.sort()
        xcs = np.array(xcs)
        yd_list = [self.yd[xc] for xc in xcs]
        # yd_list = list(self.yd.values())

        # Step 3: For each defined slope, check that the grid is consistent with the slope
        #  - cycle through moving left to right and bot to top
        #  - if not consistent then change thickness of elements in zones above and below on right side.
        mdirs = [1, -1]  # TODO: alternative between forward and reverse add
        dd = 0
        mdir = mdirs[dd]
        old_hash = ''
        for pp in range(100):
            sds = self.sds[::mdir]
            csum_y_blocks = [np.cumsum(self.y_blocks[xcs]) for xcs in self.y_blocks]
            fblocks = np.array([j for i in csum_y_blocks for j in i], dtype=int)
            new_hash = hashlib.md5(fblocks).hexdigest()
            if new_hash == old_hash:
                break
            old_hash = new_hash
            for qq, sd in enumerate(sds):
                csum_y_blocks = [np.cumsum(self.y_blocks[xcs]) for xcs in self.y_blocks]
                if mdir == 1:
                    x0 = sd[0][0]
                    x1 = sd[0][1]
                    y0 = sd[1][0]
                    y1 = sd[1][1]
                else:
                    x0 = sd[0][1]
                    x1 = sd[0][0]
                    y0 = sd[1][1]
                    y1 = sd[1][0]
                ind_x0 = int(np.argmin(abs(xcs - x0)))
                ind_x1 = int(np.argmin(abs(xcs - x1)))
                ind_y0 = int(np.argmin(abs(np.array(yd_list[ind_x0]) - y0)))
                ind_y1 = int(np.argmin(abs(np.array(yd_list[ind_x1]) - y1)))
                x1_c = xcs[ind_x1]
                y1_c = yd_list[ind_x1][ind_y1]
                nb0 = csum_y_blocks[ind_x0][ind_y0 - 1]
                nb1 = csum_y_blocks[ind_x1][ind_y1 - 1]
                sgn = int(np.sign(y1 - y0))

                dh_dzone = y1 - y0
                slope = dh_dzone / (x1 - x0)
                if abs(slope) < self.allowable_slope and nb0 == nb1:
                    continue
                if abs(slope) > self.allowable_slope and self.smooth_surf:  # TODO: and on surface and n1 - n0 sign is same
                    y_surf0 = np.interp(x0, self.x_surf, self.y_surf)
                    y_surf1 = np.interp(x1, self.x_surf, self.y_surf)
                    if np.isclose(y_surf0, y0, atol=self.dy_target*0.1) and np.isclose(y_surf1, y1, atol=self.dy_target*0.1):
                        if nb1 >= nb1 and slope > 0:
                            continue
                        if nb1 <= nb1 and slope < 0:
                            continue
                diff_nb = nb1 - nb0
                y1_below = yd_list[ind_x1][ind_y1 - 1]
                if y1_c == self.y_surf_at_xcs[x1_c]:  # surface
                    y1_above = None
                    try:
                        x_next = xcs[ind_x1 + 1]
                        y_next_surf = self.y_surf_at_xcs[x_next]
                        ind_y_next = int(np.argmin(abs(np.array(yd_list[ind_x1 + 1]) - y_next_surf)))
                        nb_next = csum_y_blocks[ind_x1 + 1][ind_y_next - 1]
                    except IndexError:
                        x_next = None
                        y_next_surf = None
                        ind_y_next = None
                else:
                    y1_above = yd_list[ind_x1][ind_y1 + 1]
                    x_next = None
                    y_next_surf = None
                    ind_y_next = None

                while sgn != np.sign(diff_nb) and diff_nb != 0:

                    nb_below = self.y_blocks[x1_c][ind_y1 - 1]
                    if nb_below + np.sign(diff_nb) * -1 == 0:
                        break
                    new_dh_below = (y1_c - y1_below) / (nb_below + np.sign(diff_nb) * -1)
                    if not (min_dh < new_dh_below < max_dh):
                        break

                    nb1 += np.sign(diff_nb) * -1
                    if y1_c != self.y_surf_at_xcs[x1_c]:
                        nb_above = self.y_blocks[x1_c][ind_y1]
                        if nb_above + np.sign(diff_nb) * 1 == 0:
                            break
                        new_dh_above = (y1_above - y1_c) / (nb_above + np.sign(diff_nb) * 1)
                        if not (min_dh < new_dh_above < max_dh):
                            break
                        self.y_blocks[x1_c][ind_y1] += np.sign(diff_nb) * 1
                    else:  # check slope of surface is appropriate
                        a = 1
                        # new_dh_next = (y_next_surf - y1_above) / (nb_next - (nb_above + np.sign(diff_nb) * 1))
                        # if not (min_dh < new_dh_above < max_dh):
                        #     break
                    self.y_blocks[x1_c][ind_y1 - 1] += np.sign(diff_nb) * -1
                    diff_nb = nb1 - nb0
                approx_grid_slope = (dh_dzone - diff_nb * self.dy_target) / (x1 - x0)
                if sgn != np.sign(approx_grid_slope):
                    pass  # this can be an issue if it cannot be adjusted
                if sgn * approx_grid_slope > self.allowable_slope:
                    nn = 0
                    while sgn * approx_grid_slope > self.allowable_slope:
                        nn += 1
                        # if no issues then adjust blocks
                        self.y_blocks[x1_c][ind_y1 - 1] += sgn * 1
                        nb1 += sgn * 1
                        diff_nb = nb1 - nb0
                        if y1_c != self.y_surf_at_xcs[x1_c]:
                            self.y_blocks[x1_c][ind_y1] += sgn * -1
                        approx_grid_slope = (dh_dzone - diff_nb * self.dy_target) / (x1 - x0)
                        if nn > 10:
                            raise ValueError
                diff_nb = nb1 - nb0
                if diff_nb:  # if zero then slope matches the line
                    # else check if an adjustment is possible
                    nnn = abs(diff_nb)
                    for nn in range(nnn):
                        diff_nb = nb1 - nb0
                        if diff_nb == 0:
                            break
                        nb_sgn = np.sign(diff_nb)
                        approx_new_slope = (dh_dzone - (diff_nb - nb_sgn * (nn + 1)) * self.dy_target) / (x1 - x0)
                        if sgn * approx_new_slope > self.allowable_slope:
                            break
                        nb_below = self.y_blocks[x1_c][ind_y1 - 1]
                        new_nb_below = nb_below + nb_sgn * -1
                        use_2_below = False
                        if new_nb_below == 0:  # try bring from even lower layer
                            nb_2_below = self.y_blocks[x1_c][ind_y1 - 2]
                            new_nb_2_below = nb_2_below + nb_sgn * -1
                            y1_2_below = yd_list[ind_x1][ind_y1 - 2]
                            if new_nb_2_below == 0:
                                break
                            new_dh_2_below = (y1_below - y1_2_below) / new_nb_2_below
                            if min_dh < new_dh_2_below < max_dh:
                                use_2_below = True
                            else:
                                break
                        else:
                            new_dh_below = (y1_c - y1_below) / (nb_below + nb_sgn * -1)
                            if not (min_dh < new_dh_below < max_dh):
                                break
                        if y1_above is not None:
                            nb_above = self.y_blocks[x1_c][ind_y1]
                            if nb_above + nb_sgn * 1 == 0:
                                break
                            new_dh_above = (y1_above - y1_c) / (nb_above + nb_sgn * 1)
                            if not (min_dh < new_dh_above < max_dh):
                                break
                        elif y_next_surf is not None:
                            if abs(nb_next - (nb1 + nb_sgn * -1)) < 2:
                                pass
                            else:
                                new_dh_on_next_surf = (y_next_surf - y1_c) / (nb_next - (nb1 + nb_sgn * -1))
                                if not (min_dh < new_dh_on_next_surf < max_dh):
                                    break
                        # if no issues then adjust blocks
                        if use_2_below:
                            self.y_blocks[x1_c][ind_y1 - 2] += nb_sgn * -1
                        else:
                            self.y_blocks[x1_c][ind_y1 - 1] += nb_sgn * -1
                        nb1 += nb_sgn * -1
                        if y1_above is not None:
                            self.y_blocks[x1_c][ind_y1] += nb_sgn * 1

        # Step 5: Set the total number of blocks to be equal to the column that uses the maximum number of
        # blocks used to get to the surface
        n_blocks = np.array([sum(self.y_blocks[xc]) for xc in xcs])
        y_surfs = np.interp(xcs, self.x_surf, self.y_surf)
        nbs_at_surf = []
        surf_inds = []
        for i in range(len(xcs)):
            x0 = xcs[i]
            nbs = np.cumsum(self.y_blocks[x0])
            nbs = np.insert(nbs, 0, 0)
            surf_inds.append(np.where(self.yd[x0] >= y_surfs[i] - 0.01)[0][0])
            nbs_at_surf.append(nbs[np.where(self.yd[x0] >= y_surfs[i] - 0.01)][0])

        # inds = np.where(np.interp(xcs, self.x_surf, self.y_surf) == h_max)[0]
        i_max = np.argmax(nbs_at_surf)  # maximum number of blocks at top
        n_max = nbs_at_surf[i_max]
        # create null nodes
        for i in range(len(xcs)):
            x0 = xcs[i]
            if n_blocks[i] != n_max:
                n_extra = n_max - n_blocks[i]  # TODO: could improve this by minus eles more evenly from zones
                if n_extra:
                    if surf_inds[i] == len(self.y_blocks[x0]):
                        self.y_blocks[x0].append(0)
                        self.yd[x0] = np.insert(self.yd[x0], len(self.yd[x0]), self.yd[x0][-1])
                self.y_blocks[x0][-1] += n_extra
                assert min(self.y_blocks[x0][:surf_inds[i]]) > 0, (x0, self.yd[x0], self.y_blocks[x0][-1])

    def trim_grid_to_target_dh(self):
        """Check mesh for potential thin layers and try to remove rows of elements to get elements close to target dh"""
        xcs = self.xcs_sorted
        opt_low = self.dy_target * (self.min_scale + 1) / 2
        opt_high = self.dy_target * (self.max_scale + 1) / 2
        y_surfs_at_xcs = np.interp(xcs, self.x_surf, self.y_surf)
        # try to trim mesh to be closer to target dh
        # First try to remove blocks
        opts_tried = []
        for nn in range(10):
            y_coords_at_xcs = [list(self.yd[xc]) for xc in xcs]
            y_node_nums_at_xcs = [list(np.cumsum(self.y_blocks[xcs])) for xcs in self.y_blocks]
            for i in range(len(y_node_nums_at_xcs)):
                y_node_nums_at_xcs[i].insert(0, 0)
                if y_node_nums_at_xcs[i][-2] == y_node_nums_at_xcs[i][-1]:
                    y_coords_at_xcs[i] = y_coords_at_xcs[i][:-1]
                    y_node_nums_at_xcs[i] = y_node_nums_at_xcs[i][:-1]
            av_dhs = []
            min_dhs = []
            for i in range(len(y_node_nums_at_xcs)):
                av_dhs.append([])
                for j in range(len(y_node_nums_at_xcs[i]) - 1):
                    if (i, j) in opts_tried or y_coords_at_xcs[i][j + 1] > y_surfs_at_xcs[i]:
                        av_dhs[i].append(1000)
                        continue
                    nb = y_node_nums_at_xcs[i][j + 1] - y_node_nums_at_xcs[i][j]
                    if nb == 0:
                        continue
                    av_dhs[i].append((y_coords_at_xcs[i][j + 1] - y_coords_at_xcs[i][j]) / nb)

                min_dhs.append(min(av_dhs[i]))
            if min(min_dhs) < self.dy_target:  # favour slightly larger elements - could use opt_low
                x_ind = min_dhs.index(min(min_dhs))
                y_ind = av_dhs[x_ind].index(min_dhs[x_ind])
                nb_lowest_p = y_node_nums_at_xcs[x_ind][y_ind]  # range where element could be removed
                nb_highest_p = y_node_nums_at_xcs[x_ind][y_ind + 1]
                if nb_lowest_p >= nb_highest_p:
                    opts_tried.append((x_ind, y_ind))
                    continue
                hzone_p = y_coords_at_xcs[x_ind][y_ind + 1] - y_coords_at_xcs[x_ind][y_ind]

                found_opt = 0
                max_new_dhs = []
                for opt in range(nb_lowest_p, nb_highest_p):
                    if nb_highest_p - nb_lowest_p - 1 == 0:
                        break
                    max_new_dh = hzone_p / (nb_highest_p - nb_lowest_p - 1)

                    for w in range(len(y_node_nums_at_xcs)):
                        y_ind = interp_left(opt, y_node_nums_at_xcs[w])
                        if y_ind == len(y_node_nums_at_xcs[w]) - 1:
                            y_ind -= 1
                        nb_low = y_node_nums_at_xcs[w][y_ind]
                        nb_high = y_node_nums_at_xcs[w][y_ind + 1]
                        hzone = y_coords_at_xcs[w][y_ind + 1] - y_coords_at_xcs[w][y_ind]
                        if (nb_high - nb_low - 1) == 0:
                            new_dh = 1e10
                        else:
                            new_dh = hzone / (nb_high - nb_low - 1)
                        if max_new_dh < new_dh:
                            max_new_dh = new_dh
                    max_new_dhs.append(max_new_dh)
                if len(max_new_dhs):
                    max_new_dh = min(max_new_dhs)
                    yind = max_new_dhs.index(max_new_dh) + nb_lowest_p
                    if max_new_dh < opt_high:
                        for w in range(len(y_node_nums_at_xcs)):
                            y_ind = interp_left(yind, y_node_nums_at_xcs[w])
                            if y_ind == len(y_node_nums_at_xcs[w]) - 1:
                                y_ind -= 1
                            self.y_blocks[xcs[w]][y_ind] -= 1
                        found_opt = 1
                if not found_opt:
                    opts_tried.append((x_ind, y_ind))
            else:
                break
        # Then try to add blocks
        opts_tried = []
        for nn in range(20):
            y_coords_at_xcs = [list(self.yd[xc]) for xc in xcs]
            y_node_nums_at_xcs = [list(np.cumsum(self.y_blocks[xcs])) for xcs in self.y_blocks]
            for i in range(len(y_node_nums_at_xcs)):
                y_node_nums_at_xcs[i].insert(0, 0)
                if y_node_nums_at_xcs[i][-2] == y_node_nums_at_xcs[i][-1]:
                    y_coords_at_xcs[i] = y_coords_at_xcs[i][:-1]
                    y_node_nums_at_xcs[i] = y_node_nums_at_xcs[i][:-1]
            av_dhs = []
            max_dhs = []
            for i in range(len(y_node_nums_at_xcs)):
                av_dhs.append([])
                for j in range(len(y_node_nums_at_xcs[i]) - 1):
                    if (i, j) in opts_tried or y_coords_at_xcs[i][j + 1] > y_surfs_at_xcs[i]:
                        av_dhs[i].append(-1)
                        continue
                    nb = y_node_nums_at_xcs[i][j + 1] - y_node_nums_at_xcs[i][j]
                    if nb == 0:
                        av_dhs[i].append(1e9)
                    else:
                        av_dhs[i].append((y_coords_at_xcs[i][j + 1] - y_coords_at_xcs[i][j]) / nb)

                max_dhs.append(max(av_dhs[i]))
            if max(max_dhs) > opt_high:
                x_ind = max_dhs.index(max(max_dhs))
                y_ind = av_dhs[x_ind].index(max_dhs[x_ind])
                nb_lowest = y_node_nums_at_xcs[x_ind][y_ind]  # range where element could be added
                nb_highest = y_node_nums_at_xcs[x_ind][y_ind + 1]
                if nb_highest <= nb_lowest:
                    opts_tried.append((x_ind, y_ind))
                    continue
                hzone_p = y_coords_at_xcs[x_ind][y_ind + 1] - y_coords_at_xcs[x_ind][y_ind]
                found_opt = 0
                min_new_dhs = []
                for opt in range(nb_lowest, nb_highest):
                    min_new_dh = hzone_p / (nb_highest - nb_lowest + 1)
                    for w in range(len(y_node_nums_at_xcs)):
                        y_ind = interp_left(opt, y_node_nums_at_xcs[w])
                        nb_low = y_node_nums_at_xcs[w][y_ind]
                        nb_high = y_node_nums_at_xcs[w][y_ind + 1]
                        hzone = y_coords_at_xcs[w][y_ind + 1] - y_coords_at_xcs[w][y_ind]
                        new_dh = hzone / (nb_high - nb_low + 1)
                        if min_new_dh > new_dh:
                            min_new_dh = new_dh
                    min_new_dhs.append(min_new_dh)
                min_new_dh = max(min_new_dhs)
                yind = min_new_dhs.index(min_new_dh) + nb_lowest
                if min_new_dh > opt_low:
                    for w in range(len(y_node_nums_at_xcs)):
                        y_ind0 = interp_left(yind, y_node_nums_at_xcs[w])
                        # y_ind1 = interp_left(nb_highest, y_node_nums_at_xcs[w])
                        self.y_blocks[xcs[w]][y_ind0] += 1
                    found_opt = 1
                if not found_opt:
                    opts_tried.append((x_ind, y_ind))
            else:
                break
        smallest = 0
        for xcs in self.y_blocks:
            if self.y_blocks[xcs][-1] < smallest:
                smallest = self.y_blocks[xcs][-1]
        if smallest != 0:
            for xcs in self.y_blocks:
                self.y_blocks[xcs][-1] += abs(smallest)

        min_h = 1e6
        max_h = 0
        for xcs in self.y_blocks:
            if max(self.y_blocks[xcs]) > max_h:
                max_h = max(self.y_blocks[xcs])
            if min(self.y_blocks[xcs]) < min_h:
                min_h = min(self.y_blocks[xcs])
        print('min_h: ', min_h)
        print('max_h: ', max_h)

    def build_req_y_node_positions(self):
        """
        Creates lists of required positions and number of elements for each significant vertical line

        Note: It also tries to make sure that steps in slopes are horizontal
        """
        min_dh = self.min_scale * self.dy_target
        max_dh = self.max_scale * self.dy_target
        xcs = self.xcs_sorted
        # Step 1: build lists containing required y element numbers and y-coords
        req_y_coords_at_xcs = [list(self.yd[xc]) for xc in xcs]
        y_node_nums_at_xcs = [list(np.cumsum(self.y_blocks[xcs])) for xcs in self.y_blocks]
        for i in range(len(y_node_nums_at_xcs)):
            y_node_nums_at_xcs[i].insert(0, 0)
            if y_node_nums_at_xcs[i][-2] == y_node_nums_at_xcs[i][-1]:
                req_y_coords_at_xcs[i] = req_y_coords_at_xcs[i][:-1]
                y_node_nums_at_xcs[i] = y_node_nums_at_xcs[i][:-1]
        # Step 2: For each slope that has a step, add additional requirement that slope does not decrease during step
        # sds = self.sds
        # for sd in sds:
        #     x0 = sd[0][0]
        #     x1 = sd[0][1]
        #     y0 = sd[1][0]
        #     y1 = sd[1][1]
        #     ind_x0 = int(np.argmin(abs(xcs - x0)))
        #     ind_x1 = int(np.argmin(abs(xcs - x1)))
        #     ind_y0 = int(np.argmin(abs(np.array(req_y_coords_at_xcs[ind_x0]) - y0)))
        #     ind_y1 = int(np.argmin(abs(np.array(req_y_coords_at_xcs[ind_x1]) - y1)))
        #     y0_c = req_y_coords_at_xcs[ind_x0][ind_y0]
        #     nb0 = y_node_nums_at_xcs[ind_x0][ind_y0]
        #     nb1 = y_node_nums_at_xcs[ind_x1][ind_y1]
        #     if nb0 != nb1:
        #         diff_nb = nb1 - nb0
        #         new_nb = y_node_nums_at_xcs[ind_x1][ind_y1] - diff_nb
        #         if new_nb not in y_node_nums_at_xcs[ind_x1]:
        #             dh_upper = (req_y_coords_at_xcs[ind_x1][ind_y1] - y0_c) / diff_nb
        #             if ind_y1 - 2 < 0:
        #                 nb_lower = nb1 - diff_nb
        #             else:
        #                 nb_lower = nb1 - y_node_nums_at_xcs[ind_x1][ind_y1 - 1] - diff_nb
        #             dh_lower = (y0_c - req_y_coords_at_xcs[ind_x1][ind_y1 - 1]) / nb_lower
        #             if min_dh < dh_upper < max_dh and min_dh < dh_lower < max_dh:
        #                 y_node_nums_at_xcs[ind_x1].append(new_nb)
        #                 y_node_nums_at_xcs[ind_x1].sort()
        #                 req_y_coords_at_xcs[ind_x1].append(y0_c)
        #                 req_y_coords_at_xcs[ind_x1].sort()

        # Step 3: Build node number lists
        req_y_nodes = []
        for i, xc0 in enumerate(xcs):
            req_y_nodes.append(list(np.array(y_node_nums_at_xcs[i]) + 1))
            req_y_nodes[i][0] = 0
            req_y_nodes[i] = np.array(req_y_nodes[i])
            req_y_coords_at_xcs[i] = np.array(req_y_coords_at_xcs[i])
            for j in range(len(req_y_coords_at_xcs[i]) - 1):
                if req_y_coords_at_xcs[i][-1 - j] == req_y_coords_at_xcs[i][-2 - j]:
                    # print(req_y_nodes[i])
                    n_eles = req_y_nodes[i][-1 - j] - req_y_nodes[i][-2 - j]
                    dh = self.dy_target * n_eles
                    req_y_coords_at_xcs[i][-1 - j] += n_eles
                    # print(req_y_coords_at_xcs[i])
                    # raise ValueError
        self.req_y_nodes = req_y_nodes
        self.req_y_coords_at_xcs = req_y_coords_at_xcs

    def build_y_coords_at_xcs(self):
        """Creates the y-coordinates for each node along each significant vertical line"""
        xcs = self.xcs_sorted
        req_y_nodes = self.req_y_nodes
        y_coords_at_xcs = self.req_y_coords_at_xcs
        # max_nbs = np.max(req_y_nodes)
        nbs_at_surf = []
        for i, xc0 in enumerate(xcs):
            nbs_at_surf.append(req_y_nodes[i][np.where(y_coords_at_xcs[i] >= self.y_surf_at_xcs[xc0])][0])

        # lower the y coordinates of unused to be inline with the right hand used blocks
        for i, xc0 in enumerate(xcs[::-1]):
            # print(i, xc0, nbs_at_surf[-i], nbs_at_surf[-1 - i])
            if i == 0:
                continue
            if nbs_at_surf[-1 - i] < nbs_at_surf[-i]:  # if there are more blocks in one to right
                diff_nbs = nbs_at_surf[-i] - nbs_at_surf[-1 - i]
                min_h = self.y_surf_at_xcs[xc0] + diff_nbs * self.dy_target * 0.5
                if nbs_at_surf[-i] in req_y_nodes[-1 - i]:
                    ind = np.argmin(abs(nbs_at_surf[-i] - req_y_nodes[-1 - i]))
                    y_coords_at_xcs[-1 - i][ind] = max([self.y_surf_at_xcs[xcs[-i]], min_h])
                else:
                    ind = np.where(req_y_nodes[-1 - i] > nbs_at_surf[-i])[0][0]
                    req_y_nodes[-1 - i] = np.insert(req_y_nodes[-1 - i], ind, nbs_at_surf[-i])
                    y_coords_at_xcs[-1 - i] = np.insert(y_coords_at_xcs[-1 - i], ind, self.y_surf_at_xcs[xcs[-i]])
            ind = np.where(req_y_nodes[-1 - i] >= nbs_at_surf[-1 - i])[0][0]
            if req_y_nodes[-1 - i][ind] != req_y_nodes[-1 - i][-1]:  # if there are blocks above the surface
                y_coords_at_xcs[-1 - i][ind + 1:] = np.interp(req_y_nodes[-1 - i][ind + 1:], req_y_nodes[-i],
                                                              y_coords_at_xcs[-i])

        # Step 4: position additional nodes to be consistent with previous column - otherwise equally spaced
        y_nodes = []
        for i, xc0 in enumerate(xcs):
            if i == 0:  # first column just interpolate
                y_nodes.append(np.interp(np.arange(req_y_nodes[i][-1] + 1), req_y_nodes[i], y_coords_at_xcs[i]))
                continue

            new_y_vals = []
            for j in range(len(y_nodes[i - 1])):
                if j not in req_y_nodes[i]:
                    # if it exceeds surface of left column then interpolate the rest
                    if 1 == 0:
                        # if y_nodes[i - 1][j] >= self.y_surf_at_xcs[xcs[i - 1]]:
                        pass
                        # if y_nodes[i-1][j] >= self.y_surf_at_xcs[xcs[i-1]]:
                        #     node_nums = [x for x in req_y_nodes[i]]
                        #     y_poses = [x for x in y_coords_at_xcs[i]]
                        #     for nn in range(len(new_y_vals)):
                        #         if nn not in node_nums:
                        #             node_nums.append(nn)
                        #             y_poses.append(new_y_vals[nn])
                        #
                        #     node_nums.sort()
                        #     y_poses.sort()
                        #     yys = np.interp(np.arange(j, req_y_nodes[i][-1] + 1), node_nums, y_poses)
                        #     new_y_vals += list(yys)
                        #     break
                    else:
                        # get next and previous req points and check the slope of each of the those back to left col
                        ind_below = interp_left(j, req_y_nodes[i])
                        req_n_below = req_y_nodes[i][ind_below]
                        req_n_above = req_y_nodes[i][ind_below + 1]
                        # sf is slope below plus slope above times j / (ind_above - ind_below)
                        dh_dzone_below = y_coords_at_xcs[i][ind_below] - y_nodes[i - 1][req_n_below]
                        dh_dzone_above = y_coords_at_xcs[i][ind_below + 1] - y_nodes[i - 1][req_n_above]
                        dh = dh_dzone_below + (dh_dzone_above - dh_dzone_below) / (req_n_above - req_n_below) * (
                                    j - req_n_below)
                        new_y_vals.append(y_nodes[i - 1][j] + dh)
                else:
                    ind = np.where(req_y_nodes[i] == j)[0][0]
                    new_y_vals.append(y_coords_at_xcs[i][ind])
            new_y_vals = np.array(new_y_vals)

            # adjust positions to ensure element thickness is appropriate
            for j in range(len(req_y_nodes[i]) - 1):
                ys = new_y_vals[req_y_nodes[i][j]:req_y_nodes[i][j + 1] + 1]
                diffs = np.diff(ys)
                if len(diffs):
                    min_h = min(diffs)
                    max_h = max(diffs)
                    # h_block = ys[0] - ys[-1]
                    nbs = req_y_nodes[i][j + 1] - req_y_nodes[i][j]
                    uni_ys = np.interp(np.arange(req_y_nodes[i][j], req_y_nodes[i][j + 1] + 1), req_y_nodes[i],
                                       y_coords_at_xcs[i])
                    uni_h = min(np.diff(uni_ys))
                    if min_h / max_h < 0.7:
                        x = 0.7 - min_h / max_h
                        new_ys = (1 - x) * ys + x * uni_ys
                        new_y_vals[req_y_nodes[i][j]:req_y_nodes[i][j + 1] + 1] = new_ys
                    if nbs_at_surf[i] == req_y_nodes[i][j] and min_h < self.dy_target:
                        h0 = new_y_vals[req_y_nodes[i][j]]
                        hs = h0 + np.arange(0, nbs + 1) * self.dy_target
                        new_y_vals[req_y_nodes[i][j]:req_y_nodes[i][j + 1] + 1] = hs

            y_nodes.append(new_y_vals)

        y_nodes = np.array(y_nodes)
        # For each surface slope adjust steps so that they are not pointed against slope
        for i, xc0 in enumerate(xcs):
            if i == len(xcs) - 1:
                break
            surf_at_xc = self.y_surf_at_xcs[xc0]
            ind_yc = np.argmin(abs(y_nodes[i] - surf_at_xc))
            if ind_yc == len(y_nodes[i]) - 1:
                continue
            surf_at_next_xc = self.y_surf_at_xcs[xcs[i + 1]]
            ind_nc = np.argmin(abs(y_nodes[i + 1] - surf_at_next_xc))
            if ind_nc == ind_yc:
                continue
            diff_nb = ind_nc - ind_yc
            # assert diff_nb > 0  # currently only supports smoothing forward
            next_slope = surf_at_next_xc - surf_at_xc
            # trim either half the block or min_dh
            if next_slope > 0 and diff_nb > 0:
                ind_yc2 = np.where(y_nodes[i + 1] > surf_at_xc)[0][0]
                ind_yc2 = max(ind_yc2, ind_yc + 1)
                curr_col_ys = list(y_nodes[i][ind_yc2 - 1: ind_nc + 1])
                next_ys = list(y_nodes[i + 1][ind_yc2 - 1: ind_nc + 1])
                # y_nodes[i][ind_yc: ind_nc] = (next_ys - next_ys[0]) * 0.5 + next_ys[0]
                av_dh = next_slope / diff_nb
                update_unused = 0
                for kk in range(1, len(next_ys)):
                    a = curr_col_ys[kk] - next_ys[kk]
                    new_dh = next_ys[kk] - curr_col_ys[kk - 1]
                    if new_dh < self.dy_target * 0.5:
                        next_ys[kk] = curr_col_ys[kk - 1] + self.dy_target * 0.5

                    if (curr_col_ys[kk] - next_ys[kk]) / av_dh > 0.2:
                        update_unused = 1
                if update_unused:
                    y_nodes[i][ind_yc2: ind_nc + 1] = next_ys[1:]
            # elif next_slope < 0 and diff_nb < 0:
            #     next_ys = y_nodes[i+1][ind_yc+1: ind_nc + 1]
            #     # y_nodes[i][ind_yc: ind_nc] = (next_ys - next_ys[0]) * 0.5 + next_ys[0]
            #     y_nodes[i][ind_yc+1: ind_nc + 1] = next_ys

        self.y_coords_at_xcs = y_nodes[:, ::-1]  # invert y-values

    def build_y_coords_grid_via_propagation(self):
        """Interpolates the position of all nodes based on the y-coordinates along the significant lines"""
        if self.y_coords_at_xcs is None:
            self.build_y_coords_at_xcs()
        if self.x_nodes is None:
            self.set_x_nodes()
        self.y_nodes = interp2d(self.x_nodes, np.array(self.xcs_sorted), self.y_coords_at_xcs)

    def build_y_coords_grid_via_3d_interp(self):
        """Interpolates the position of all nodes based on the coordinates of the significant positions"""
        if self.x_nodes is None:
            self.set_x_nodes()
        y_node_nums = np.arange(0, self.req_y_nodes[0][-1] + 1)
        ys = []
        for i in range(len(self.x_nodes)):
            ys.append(
                interp3d(self.x_nodes[i], y_node_nums, self.xcs_sorted, self.req_y_nodes, self.req_y_coords_at_xcs))
        self.y_nodes = np.array(ys)

    def set_x_nodes(self):
        """Determine optimal position of node x-coordinates"""
        dxs = [0]
        x_start = 0
        x_scale_curr = self.x_scale_vals[0]
        for xx in range(1, len(self.xcs_sorted)):
            x_shift = self.xcs_sorted[xx] - self.xcs_sorted[xx - 1]
            extra_inds = np.where(
                (self.xcs_sorted[xx] > self.x_scale_pos) & (self.x_scale_pos > self.xcs_sorted[xx - 1]))
            x_cps = [self.xcs_sorted[xx - 1]]
            x_scales = [x_scale_curr]
            for i in extra_inds[0]:
                x_cps.append(self.x_scale_pos[i])
                x_scales.append(self.x_scale_vals[i])
            x_scales = np.array(x_scales)
            x_cps.append(self.xcs_sorted[xx])
            zone_widths = np.diff(x_cps)
            n_eles = np.sum(zone_widths / (x_scales * self.dy_target))
            n_x_eles = max(1, int(n_eles + 0.5))
            av_ele_width = x_shift / n_x_eles
            x_incs = []
            for n in range(n_x_eles):
                x_ele = 0
                for pp in range(10):
                    x_ele += interp_left(x_ele + x_start, self.x_scale_pos, self.x_scale_vals) * self.dy_target / 10
                x_incs.append(x_ele)
                x_start += x_ele
            x_incs = np.array(x_incs) * x_shift / sum(x_incs)
            dxs += list(x_incs)
            x_start = np.sum(dxs)
            x_scale_curr = interp_left(x_start, self.x_scale_pos, self.x_scale_vals)
            assert np.isclose(x_start, self.xcs_sorted[xx]), (x_start, self.xcs_sorted[xx])

        self.x_nodes = np.cumsum(dxs)

    def get_closest_idx_on_varyxy(self, x0, y0):
        x_diffs = abs(self.x_nodes2d - x0)
        y_diffs = abs(self.y_nodes - y0)
        dir_diffs = np.sqrt(x_diffs ** 2 + y_diffs ** 2)
        k = dir_diffs.argmin()
        ncol = dir_diffs.shape[1]
        return int(k / ncol), k % ncol

    def adjust_for_smooth_surface(self):
        """Make the surface have less than 90 degree changes"""
        self.x_nodes2d = self.x_nodes[:, np.newaxis] * np.ones_like(self.y_nodes)
        x_points = self.xcs_sorted
        x0 = x_points[0]
        y0 = np.interp(x0, self.x_surf, self.y_surf)

        for ss in range(1, len(self.x_surf)):
            x1 = x_points[ss]
            y1 = np.interp(x1, self.x_surf, self.y_surf)
            slope = (y1 - y0) / (x1 - x0)

            x0_ind, y0_ind = self.get_closest_idx_on_varyxy(x0, y0)
            x1_ind, y1_ind = self.get_closest_idx_on_varyxy(x1, y1)
            # x0_ind_alt = np.argmin(abs(self.x_nodes - x0))  # TODO: should use x_nodes2d
            # y0_ind_alt = np.argmin(abs(self.y_nodes[x0_ind] - y0))  # counts from top to bottom
            # print('inds: ', x0_ind, x0_ind_alt, y0_ind, y0_ind_alt)
            # x1_ind = np.argmin(abs(self.x_nodes - x1))
            # y1_ind = np.argmin(abs(self.y_nodes[x1_ind] - y1))
            # if x_nodes2d[x0_ind][y0_ind] != self.x_nodes[x0_ind]:
            #     # mesh already adjusted, need to get actual node coord
            #     pass
            # raise ValueError('x already moved cannot perform double adjustment')
            if y1_ind != y0_ind:  # non smooth surface
                y_ind_top = min([y0_ind, y1_ind])
                y_ind_bot = max([y0_ind, y1_ind])
                y_top = max([y0, y1])
                y_bot = min([y0, y1])
                dy_inds = abs(y1_ind - y0_ind)
                if (x1_ind - x0_ind) > self.smooth_ratio * abs(y1_ind - y0_ind):
                    # Need to smooth by adjusting each step
                    # get all relevant node y-coordinates
                    y_ns = self.y_nodes[x0_ind: x1_ind + 1, y_ind_top: y_ind_top + dy_inds + 1]
                    x_ns = self.x_nodes2d[x0_ind: x1_ind + 1, y_ind_top: y_ind_top + dy_inds + 1]
                    y_ns = y_ns[:, ::-1]  # flip
                    x_ns = x_ns[:, ::-1]

                    if y1_ind < y0_ind:  # up slope to the right
                        new_x_ns, new_y_ns = adj_slope_by_layers(x_ns, y_ns)
                        self.x_nodes2d[x0_ind: x1_ind + 1, y_ind_top: y_ind_top + dy_inds + 1] = new_x_ns[:, ::-1]
                        self.y_nodes[x0_ind: x1_ind + 1, y_ind_top: y_ind_top + dy_inds + 1] = new_y_ns[:, ::-1]

                    else:  # down slope to the right
                        new_x_ns, new_y_ns = adj_slope_by_layers(x_ns, -y_ns, -1)
                        new_y_ns *= -1
                        self.x_nodes2d[x0_ind: x1_ind + 1, y_ind_top: y_ind_top + dy_inds + 1] = new_x_ns[:, ::-1]
                        self.y_nodes[x0_ind: x1_ind + 1, y_ind_top: y_ind_top + dy_inds + 1] = new_y_ns[:, ::-1]
                else:  # Smooth the whole slope as one
                    dx = x1 - x0

                    if y1_ind > y0_ind:  # slope moves down as you go to the right
                        x_rhs_ind = x1_ind
                        x_lhs = x0 - dx
                        x0_ind = np.argmin(abs(self.x_nodes - x0))
                        x_lhs_ind = np.argmin(abs(self.x_nodes - x_lhs))

                        y_lhs = self.y_nodes[x_lhs_ind, y_ind_top: y_ind_bot + 1]
                        x_short_vals_lower = self.x_nodes2d[x0_ind:x_rhs_ind + 1, y_ind_bot]
                        x_incs = x_short_vals_lower - x_short_vals_lower[0]
                        y_lower = np.interp(x_incs, [x_incs[0], x_incs[-1]], [y_lhs[-1], y1])
                        sf = (y0 - y_lower) / (y_lhs[0] - y_lhs[-1]) * np.ones_like(y_lower)
                        ys = (y_lhs - y_lhs[-1])[np.newaxis, :] * sf[:, np.newaxis] + y_lower[:, np.newaxis]
                        self.y_nodes[x0_ind:x_rhs_ind + 1, y_ind_top: y_ind_bot + 1] = ys
                        dxs = np.linspace(0, dx, x_rhs_ind - x_lhs_ind + 1)
                        x_vals_upper = self.x_nodes2d[x_lhs_ind:x_rhs_ind + 1, y_ind_top] - dxs
                        x_vals_lower = self.x_nodes2d[x_lhs_ind:x_rhs_ind + 1, y_ind_bot]
                        y_hs = self.y_nodes[x1_ind][y_ind_top: y_ind_bot + 1][::-1]
                        xvs = interp2d(y_hs, [y_bot, y_top], [x_vals_lower, x_vals_upper])[::-1]
                        self.x_nodes2d[x_lhs_ind:x_rhs_ind + 1, y_ind_top: y_ind_bot + 1] = xvs.T
                    else:  # slope moves down as you go to the left
                        i_curr = np.where(self.xcs_sorted == x1)[0][0]
                        if i_curr == len(self.xcs_sorted) - 1:
                            x_rhs = self.xcs_sorted[i_curr]
                        else:
                            x_rhs = min([x1 + 2 * (x1 - x0), self.xcs_sorted[i_curr + 1]])
                        xrhs_ind = np.argmin(abs(self.x_nodes - x_rhs))
                        x_rhs = self.x_nodes[xrhs_ind]
                        x_vals_upper = np.linspace(x1, x_rhs, xrhs_ind - x0_ind + 1)
                        x_vals_lower = self.x_nodes2d[x0_ind:xrhs_ind + 1, y1_ind]

                        n_eles = len(self.y_nodes[x0_ind][y1_ind: y0_ind + 1])
                        for xx in range(x0_ind, x1_ind):
                            dy = y1 - self.y_nodes[xx][y1_ind: y0_ind + 1][0]
                            dinc = dy / max(n_eles - 1, 1) * np.arange(n_eles)[::-1]
                            self.y_nodes[xx][y1_ind: y0_ind + 1] += dinc
                        y_hs = self.y_nodes[x0_ind][y1_ind: y0_ind + 1][::-1]
                        xvs = interp2d(y_hs, [y0, y1], [x_vals_lower, x_vals_upper])[::-1]
                        self.x_nodes2d[x0_ind:xrhs_ind + 1, y1_ind: y0_ind + 1] = xvs.T
                        # y_lhs = self.y_nodes[x0, y1_ind: y0_ind + 1]
                        # sf = (y0 - y1) / (y_lhs[-1] - y_lhs[0])
                        # y_rhs = y_lhs * sf + y1 - y_lhs[0]

            x0 = x1
            y0 = y1
        pass

    @property
    def soils(self):
        return self._soils

    def set_to_decimal_places(self):
        """Adjusts the node coordinates to a certain number of decimal places"""
        self.y_nodes = np.round(self.y_nodes, self.dp)
        self.x_nodes = np.round(self.x_nodes, self.dp)

    def set_soil_ids_to_vary_y_grid(self):
        # Assign soil to element grid
        x_centres = (self.x_nodes[:-1] + self.x_nodes[1:]) / 2
        y_centres = (self.y_nodes[:, :-1] + self.y_nodes[:, 1:]) / 2
        y_centres = (y_centres[:-1] + y_centres[1:]) / 2
        self.y_centres = y_centres
        surf_centres = np.interp(x_centres, self.tds.x_surf, self.tds.y_surf)
        self.soil_grid = np.zeros((len(y_centres), len(y_centres[0])), dtype=int)
        self.x_index_to_sp_index = interp_left(x_centres, self.tds.x_sps, np.arange(0, len(self.tds.x_sps)))
        self.x_index_to_sp_index = np.array(self.x_index_to_sp_index, dtype=int)
        for xx in range(len(self.soil_grid)):
            for yy in range(len(self.soil_grid[0])):
                pid = self.x_index_to_sp_index[xx]
                sp = self.tds.sps[pid]
                if y_centres[xx][yy] > surf_centres[xx]:
                    self.soil_grid[xx][yy] = self._inactive_value
                    continue
                x_angles = list(sp.x_angles)
                sp_x = self.tds.x_sps[pid]
                for ll in range(1, sp.n_layers + 1):
                    yc = y_centres[xx][yy]
                    if x_angles[ll - 1] is None:
                        pass
                    elif -yc > (
                            sp.layer_depth(ll) - x_angles[ll - 1] * (x_centres[xx] - sp_x) - self.y_surf_at_sps[pid]):
                        pass
                    else:
                        if ll == 1:  # above the original soil profile due to ground slope
                            unique_hash = sp.layer(1).unique_hash
                        else:
                            unique_hash = sp.layer(ll - 1).unique_hash
                        self.soil_grid[xx][yy] = self._soil_hashes.index(unique_hash)
                        break
                    if ll == sp.n_layers:
                        unique_hash = sp.layer(ll).unique_hash
                        self.soil_grid[xx][yy] = self._soil_hashes.index(unique_hash)
                        break

    def set_soil_ids_to_vary_xy_grid(self):
        # Assign soil to element grid
        x_centres = (self.x_nodes2d[:-1, :] + self.x_nodes2d[1:, :]) / 2
        x_centres = (x_centres[:, :-1] + x_centres[:, 1:]) / 2
        y_centres = (self.y_nodes[:, :-1] + self.y_nodes[:, 1:]) / 2
        y_centres = (y_centres[:-1] + y_centres[1:]) / 2
        self.y_centres = y_centres
        self.soil_grid = np.zeros((len(y_centres), len(y_centres[0])), dtype=int)
        self.x_index_to_sp_index = interp_left(x_centres[:, -1], self.tds.x_sps, np.arange(0, len(self.tds.x_sps)))
        self.x_index_to_sp_index = np.array(self.x_index_to_sp_index, dtype=int)
        for xx in range(len(self.soil_grid)):
            for yy in range(len(self.soil_grid[0])):
                pid = self.x_index_to_sp_index[xx]
                sp = self.tds.sps[pid]
                if y_centres[xx][yy] > np.interp(x_centres[xx][yy], self.x_surf, self.y_surf):
                    self.soil_grid[xx][yy] = self._inactive_value
                    continue
                x_angles = list(sp.x_angles)
                sp_x = self.tds.x_sps[pid]
                lay_ind = 0
                for ll in range(1, sp.n_layers + 1):
                    # yc = y_centres[xx][yy]
                    x_diff = x_centres[xx][yy] - sp_x
                    z_lay_at_sp = -sp.layer_depth(ll) + self.y_surf_at_sps[pid]
                    if x_angles[ll - 1] is None or np.isnan(x_angles[ll - 1]):
                        z_lay_at_x = 1e6
                    else:
                        z_lay_at_x = z_lay_at_sp + x_angles[ll - 1] * x_diff
                    if y_centres[xx][yy] <= z_lay_at_x:
                        lay_ind = ll
                    else:
                        break
                if lay_ind == 0:
                    self.soil_grid[xx][yy] = self._inactive_value
                else:
                    unique_hash = sp.layer(lay_ind).unique_hash
                    self.soil_grid[xx][yy] = self._soil_hashes.index(unique_hash)
                    # else:
                    #     if ll == 1:  # above the original soil profile due to ground slope
                    #         unique_hash = sp.layer(1).unique_hash
                    #     else:
                    #         unique_hash = sp.layer(ll - 1).unique_hash
                    #
                    #     break
                    # if ll == sp.n_layers:
                    #     unique_hash = sp.layer(ll).unique_hash
                    #     self.soil_grid[xx][yy] = self._soil_hashes.index(unique_hash)
                    #     break

    def create_mesh(self):
        # if len(np.shape(self.x_nodes)) == 2:
        if self.x_nodes2d is not None:
            self._femesh = FiniteElementVaryXY2DMesh(self.x_nodes2d, self.y_nodes, self.soil_grid, self.soils)
        else:
            self._femesh = FiniteElementVaryY2DMesh(self.x_nodes, self.y_nodes, self.soil_grid, self.soils)

    @property
    def femesh(self):
        return self._femesh

    def exclude_fd_eles(self):  # TODO: implement a near field option, where grid gets remeshed with angles to have more detail near footing
        for i, bd in enumerate(self.tds.bds):
            fd = bd.fd
            fcx = self.tds.x_bds[i] + bd.x_fd
            fcy = np.interp(fcx, self.x_surf, self.y_surf)
            lip = getattr(fd, fd.ip_axis)
            x0 = fcx - lip / 2
            x1 = fcx + lip / 2
            y_top = fcy - fd.depth
            y_bot = fcy - fd.depth + fd.height
            xsi = self.femesh.get_nearest_node_index_at_x(x0)
            xei = self.femesh.get_nearest_node_index_at_x(x1)
            yei = self.femesh.get_nearest_node_index_at_depth(y_top, x0)
            ysi = self.femesh.get_nearest_node_index_at_depth(y_bot, x0)
            # create foundation nodes a soil mesh nodes
            # along the base
            j = 0
            for xx in range(int(xsi), int(xei)):
                for yy in range(int(ysi), int(yei)):
                    self.soil_grid[xx][yy] = self._inactive_value
                    self.femesh.soil_grid[xx][yy] = self.femesh.inactive_value


class FiniteElementVaryY2DMesh(PhysicalObject):
    base_type = 'femesh'
    type = 'vary_y2d'

    def __init__(self, x_nodes, y_nodes, soil_grid, soils, inactive_value=1e6):
        self._x_nodes = x_nodes
        self._y_nodes = y_nodes
        self._soil_grid = soil_grid
        self._soils = soils
        self.inactive_value = inactive_value
        self.inputs = ['x_nodes', 'y_nodes', 'soil_grid', 'soils']

    def get_active_nodes(self):
        active_nodes = np.ones((len(self._x_nodes), len(self._y_nodes[0])), dtype=int)  # Start with all active
        # Pad soil_grid with inactive values around edge
        sg_w_pad = self.inactive_value * np.ones((len(self._soil_grid) + 2, len(self._soil_grid[0]) + 2))
        sg_w_pad[1:-1, 1:-1] = self._soil_grid
        # Then compute the average soil_grid from four elements
        node_grid = (sg_w_pad[:-1, :-1] + sg_w_pad[:-1, 1:] + sg_w_pad[1:, :-1] + sg_w_pad[1:, 1:]) / 4
        # if average is equal to inactive then node is not active
        inds = np.where(node_grid == self.inactive_value)
        active_nodes[inds] = 0
        return active_nodes

    @property
    def soils(self):
        return self._soils

    def get_ele_indexes_at_depths(self, depths, x, low=None):
        x_ind = self.get_ele_indexes_at_xs([x])[0]
        return interp_left(-np.array(depths), -self._y_nodes[x_ind], low=low)

    def get_ele_indexes_at_xs(self, xs, low=None):
        return interp_left(xs, self.x_nodes, low=low)

    def get_nearest_node_index_at_depth(self, depth, x):
        x_ind = self.get_nearest_node_index_at_x(x)
        return np.argmin(abs(self._y_nodes[x_ind] - depth))

    def get_nearest_node_index_at_x(self, x):
        return np.argmin(abs(self.x_nodes - x))

    @property
    def nny(self):
        return len(self._y_nodes[0])

    @property
    def nnx(self):
        return len(self._x_nodes)

    def set_to_decimal_places(self, dp):
        """Adjusts the node coordinates to a certain number of decimal places"""
        self._y_nodes = np.round(self._y_nodes, dp)
        self._x_nodes = np.round(self._x_nodes, dp)

    @property
    def x_nodes(self):
        return self._x_nodes

    @x_nodes.setter
    def x_nodes(self, x_nodes):
        if isinstance(x_nodes, str):
            self._x_nodes = np.loadtxt(x_nodes)
        else:
            self._x_nodes = x_nodes

    @property
    def y_nodes(self):
        """Y-position of nodes - top-to-bottom"""
        return self._y_nodes

    @y_nodes.setter
    def y_nodes(self, y_nodes):
        if isinstance(y_nodes, str):
            self._y_nodes = np.loadtxt(y_nodes)
        else:
            self._y_nodes = y_nodes

    @property
    def soil_grid(self):
        return self._soil_grid

    @soil_grid.setter
    def soil_grid(self, soil_grid):
        if isinstance(soil_grid, str):
            self._soil_grid = np.loadtxt(soil_grid)
        else:
            self._soil_grid = soil_grid

    def add_to_dict(self, models_dict, **kwargs):
        if self.base_type not in models_dict:
            models_dict[self.base_type] = {}
        if "soil" not in models_dict:
            models_dict["soil"] = {}

    def get_node_indices_for_all_eles(self):
        xx = np.arange(len(self.soil_grid))
        xis = np.array([xx, xx + 1, xx + 1, xx])[:, :, np.newaxis] * np.ones_like(self.soil_grid)[np.newaxis, :, :]
        yy = np.arange(len(self.soil_grid[0]))
        yis = np.array([xx, xx + 1, xx + 1, xx])[:, np.newaxis, :] * np.ones_like(self.soil_grid)[np.newaxis, :, :]
        return xis, yis

    def get_node_coords_for_all_eles(self):
        xis, yis = self.get_node_indices_for_all_eles()
        x_coords = self.x_nodes[xis]
        y_coords = self.y_nodes[xis, yis]


class FiniteElementVaryXY2DMesh(PhysicalObject):
    base_type = 'femesh'
    type = 'vary_xy2d'

    def __init__(self, x_nodes, y_nodes, soil_grid, soils, inactive_value=1e6):
        self._x_nodes = x_nodes
        self._y_nodes = y_nodes
        self.node_coords_mesh = None
        self.ele_coords_mesh = None
        self._soil_grid = soil_grid
        self._soils = soils
        self.inactive_value = inactive_value
        self.inputs = ['x_nodes', 'y_nodes', 'soil_grid', 'soils']

    def get_active_nodes(self):
        active_nodes = np.ones((len(self._x_nodes), len(self._y_nodes[0])), dtype=int)  # Start with all active
        # Pad soil_grid with inactive values around edge
        sg_w_pad = self.inactive_value * np.ones((len(self._soil_grid) + 2, len(self._soil_grid[0]) + 2))
        sg_w_pad[1:-1, 1:-1] = self._soil_grid
        # Then compute the average soil_grid from four elements
        node_grid = (sg_w_pad[:-1, :-1] + sg_w_pad[:-1, 1:] + sg_w_pad[1:, :-1] + sg_w_pad[1:, 1:]) / 4
        # if average is equal to inactive then node is not active
        inds = np.where(node_grid == self.inactive_value)
        active_nodes[inds] = 0
        return active_nodes

    @property
    def soils(self):
        return self._soils

    def tidy_unused_mesh(self):
        anodes = self.get_active_nodes()
        inds = np.where(anodes == 0)
        xns = self.x_nodes
        yns = self.y_nodes
        for i in range(len(xns)):
            inds = np.where(anodes[i] == 0)
            if len(inds[0]):
                x_surf = self.x_nodes[i][inds[0][-1] + 1]
                y_surf = self.y_nodes[i][inds[0][-1] + 1]
                xns[i][inds] = x_surf
                yns[i][inds] = y_surf + np.arange(1, len(inds[0]) + 1)[::-1]

    # def get_ele_indexes_at_depths(self, depths, x, low=None):
    #     x_ind = self.get_ele_indexes_at_xs([x])[0]
    #     return interp_left(-np.array(depths), -self._y_nodes[x_ind], low=low)
    #
    # def get_ele_indexes_at_xs(self, xs, y, low=None):
    #     return interp_left(xs, self.x_nodes, low=low)
    #
    # def get_nearest_node_index_at_depth(self, depth, x):
    #     x_ind = self.get_nearest_node_index_at_x(x)
    #     return np.argmin(abs(self._y_nodes[x_ind] - depth))
    #
    # def get_nearest_node_index_at_x(self, x, y):
    #     return np.argmin(abs(self.x_nodes - x))

    def build_node_coords_mesh(self):
        self.node_coords_mesh = np.array([self.x_nodes, self.y_nodes]).transpose(1, 2, 0)

    def build_ele_coords_mesh(self):
        x_centres = (self.x_nodes[:-1, :] + self.x_nodes[1:, :]) / 2
        x_centres = (x_centres[:, :-1] + x_centres[:, 1:]) / 2
        y_centres = (self.y_nodes[:, :-1] + self.y_nodes[:, 1:]) / 2
        y_centres = (y_centres[:-1] + y_centres[1:]) / 2
        self.ele_coords_mesh = np.array([x_centres, y_centres]).transpose(1, 2, 0)

    def get_nearest_nodes_indexes(self, coords, n=1):
        coords = np.array(coords)
        if self.node_coords_mesh is None:
            self.build_node_coords_mesh()
        norms = np.linalg.norm(coords - self.node_coords_mesh, axis=2)
        arr_s = np.shape(self.node_coords_mesh)[:-1]
        return np.dstack(np.unravel_index(np.argsort(norms.ravel())[:n], arr_s))[0]

    def get_nearest_eles_indexes(self, coords, n=1):
        coords = np.array(coords)
        if self.ele_coords_mesh is None:
            self.build_ele_coords_mesh()
        norms = np.linalg.norm(coords - self.ele_coords_mesh, axis=2)
        arr_s = np.shape(self.ele_coords_mesh)[:-1]
        return np.dstack(np.unravel_index(np.argsort(norms.ravel())[:n], arr_s))[0]

    def get_ele_index_by_type(self, stype):
        s_inds = []
        for i, sl in enumerate(self.soils):
            if sl.type == stype:
                s_inds.append(i)
        s_inds = np.array(s_inds)
        arr_s = np.shape(self.soil_grid)
        pmesh_inds = np.where(self.soil_grid.flatten() == s_inds[:, None])
        pmesh_inds = np.unravel_index(pmesh_inds[1], arr_s)
        return pmesh_inds

    @property
    def nny(self):
        return len(self._y_nodes[0])

    @property
    def nnx(self):
        return len(self._x_nodes)

    def set_to_decimal_places(self, dp):
        """Adjusts the node coordinates to a certain number of decimal places"""
        self._y_nodes = np.round(self._y_nodes, dp)
        self._x_nodes = np.round(self._x_nodes, dp)

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

    def add_to_dict(self, models_dict, **kwargs):
        if self.base_type not in models_dict:
            models_dict[self.base_type] = {}
        if "soil" not in models_dict:
            models_dict["soil"] = {}

    def get_change_coords_at_vert_ele_offset(self, tol=0):
        prev_ind = np.where(self.soil_grid[0] != self.inactive_value)[0][0]
        coords = [[self.x_nodes[0][prev_ind + 1]],
                  [self.y_nodes[0][prev_ind + 1]]]
        for i in range(self.nnx - 1):
            active_ind = np.where(self.soil_grid[i] != self.inactive_value)[0][0]
            if active_ind < prev_ind:
                coords[0].append(self.x_nodes[i + 1][prev_ind + 1])
                coords[1].append(self.y_nodes[i + 1][prev_ind + 1])
                coords[0].append(self.x_nodes[i + 1][prev_ind])
                coords[1].append(self.y_nodes[i + 1][prev_ind])
                if prev_ind != active_ind + 1:
                    coords[0].append(self.x_nodes[i + 1][active_ind + 1])
                    coords[1].append(self.y_nodes[i + 1][active_ind + 1])
            elif active_ind > prev_ind:
                coords[0] = coords[0][:-1]  # remove last added
                coords[1] = coords[1][:-1]
                coords[0].append(self.x_nodes[i - 1][active_ind])
                coords[1].append(self.y_nodes[i - 1][active_ind])
                if prev_ind != active_ind + 1:
                    coords[0].append(self.x_nodes[i - 1][active_ind + 1])
                    coords[1].append(self.y_nodes[i - 1][active_ind + 1])
                coords[0].append(self.x_nodes[i][active_ind + 1])
                coords[1].append(self.y_nodes[i][active_ind + 1])
            else:
                coords[0].append(self.x_nodes[i + 1][active_ind + 1])
                coords[1].append(self.y_nodes[i + 1][active_ind + 1])
            prev_ind = active_ind
        coords = np.array(coords)
        dx = np.clip(np.diff(coords[0]), 1.0e-9, None)
        slopes = np.diff(coords[1]) / dx
        diff_slopes = np.diff(slopes)
        inds = np.where(abs(diff_slopes) > tol)[0] + 1
        inds = np.array([0] + list(inds) + [len(coords[0]) - 1], dtype=int)
        ccoords = coords.T[inds].T
        return ccoords

    def get_surface_node_indices(self, tol=0):
        # switched = 1
        # if switched:

        prev_ind = np.where(self.soil_grid[0] != self.inactive_value)[0][0]
        inds = [[0, prev_ind]]
        for i in range(self.nnx - 1):
            active_ind = np.where(self.soil_grid[i] != self.inactive_value)[0][0]
            if active_ind < prev_ind:
                inds.append([i+1, active_ind])
                for j in range(active_ind, prev_ind):
                    inds.append([i, j])
            elif active_ind > prev_ind:
                for j in range(prev_ind+1, active_ind+1):
                    inds.append([i, j])
                inds.append([i + 1, active_ind])
            else:
                inds.append([i + 1, active_ind])
            prev_ind = active_ind
        inds = np.array(inds)
        return inds

    def get_node_indices_for_all_eles(self):
        xx = np.arange(len(self.soil_grid))
        xis = np.array([xx, xx + 1, xx + 1, xx]).T[:, np.newaxis, :] * np.ones_like(self.soil_grid)[:, :, np.newaxis]
        yy = np.arange(len(self.soil_grid[0]))
        yis = np.array([yy, yy, yy + 1, yy + 1]).T[np.newaxis, :, :] * np.ones_like(self.soil_grid)[:, :, np.newaxis]
        return xis, yis

    def get_node_coords_for_all_eles(self):
        xis, yis = self.get_node_indices_for_all_eles()
        x_coords = self.x_nodes[xis, yis]
        y_coords = self.y_nodes[xis, yis]
        return x_coords, y_coords

    def get_centroid_coords_for_all_eles(self):
        return calc_centroid(*self.get_node_coords_for_all_eles())


def construct_femesh_vary_xy(tds, dy_target, x_scale_pos=None, x_scale_vals=None, rm_fd_eles=0):
    fc = FiniteElementVary2DMeshConstructor(tds, dy_target, x_scale_pos=x_scale_pos, x_scale_vals=x_scale_vals,
                                            smooth_surf=True, rm_fd_eles=rm_fd_eles)
    femesh = fc.femesh
    assert isinstance(femesh, FiniteElementVaryXY2DMesh)
    return femesh


def construct_femesh_vary_y(tds, dy_target, x_scale_pos=None, x_scale_vals=None, rm_fd_eles=0):
    fc = FiniteElementVary2DMeshConstructor(tds, dy_target, x_scale_pos=x_scale_pos, x_scale_vals=x_scale_vals,
                                            smooth_surf=False, rm_fd_eles=rm_fd_eles)
    femesh = fc.femesh
    assert isinstance(femesh, FiniteElementVaryY2DMesh)
    return femesh


def _example_run():
    vs = 150.0
    rho = 1.8
    g_mod = vs ** 2 * rho
    import sfsimodels as sm
    sl0 = sm.Soil(g_mod=g_mod, unit_dry_weight=rho * 9.8, poissons_ratio=0.31)
    sl1 = sm.Soil(g_mod=g_mod, unit_dry_weight=rho * 9.8, poissons_ratio=0.32)
    sl2 = sm.Soil(g_mod=g_mod, unit_dry_weight=rho * 9.8, poissons_ratio=0.33)
    sl3 = sm.Soil(g_mod=g_mod, unit_dry_weight=rho * 9.8, poissons_ratio=0.34)
    sl4 = sm.Soil(g_mod=g_mod, unit_dry_weight=rho * 9.8, poissons_ratio=0.35)
    sl5 = sm.Soil(g_mod=g_mod, unit_dry_weight=rho * 9.8, poissons_ratio=0.36)
    sp = sm.SoilProfile()
    sp.add_layer(0, sl1)
    sp.add_layer(5, sl2)
    sp.add_layer(12, sl3)
    sp.height = 18
    sp.x = 0
    sp2 = sm.SoilProfile()
    sp2.add_layer(0, sl4)
    sp2.add_layer(7, sl5)
    sp2.add_layer(12, sl0)
    sp2.height = 20
    sp.x_angles = [0.01, 0.05, 0.0]
    sp2.x_angles = [0.0, 0.00, 0.0]

    fd = sm.RaftFoundation()
    fd.width = 2
    fd.depth = 0
    fd.ip_axis = 'width'
    fd.height = 1
    fd.length = 100
    tds = TwoDSystem(width=40, height=15)
    tds.add_sp(sp, x=0)
    tds.add_sp(sp2, x=14)
    tds.x_surf = np.array([0, 10, 12, 25, 40])
    tds.y_surf = np.array([0, 0, 2, 2.5, 2])
    bd = sm.NullBuilding()
    bd.set_foundation(fd, x=0.0)
    tds.add_bd(bd, x=8)

    x_scale_pos = np.array([0, 5, 15, 30])
    x_scale_vals = np.array([2., 1.0, 2.0, 3.0])
    fc = FiniteElementVary2DMeshConstructor(tds, 0.3, x_scale_pos=x_scale_pos, x_scale_vals=x_scale_vals)
    femesh = fc.femesh


def _example_simple_run():
    vs = 150.0
    rho = 1.8
    g_mod = vs ** 2 * rho
    import sfsimodels as sm
    sl = sm.Soil(g_mod=g_mod, unit_dry_weight=rho * 9.8, poissons_ratio=0.3)
    sl2 = sm.Soil(g_mod=g_mod * 2, unit_dry_weight=rho * 9.8, poissons_ratio=0.3)
    sp = sm.SoilProfile()
    sp.add_layer(0, sl)
    sp.add_layer(5, sl2)
    sp.height = 14
    sp.x = 0
    sp2 = sm.SoilProfile()
    sp2.add_layer(0, sl)
    sp2.add_layer(7, sl2)
    sp2.height = 14
    sp.x_angles = [None, 0.0]
    sp2.x_angles = [None, 0.05]
    tds = TwoDSystem(width=25, height=10)
    tds.add_sp(sp, x=0)
    tds.add_sp(sp2, x=14)
    tds.x_surf = np.array([0, 10, 10.9, 25])
    tds.y_surf = np.array([0, 0, 2, 2.3])

    x_scale_pos = np.array([0, 5, 15, 30])
    x_scale_vals = np.array([2., 1.0, 2.0, 3.0])
    fc = FiniteElementVary2DMeshConstructor(tds, 0.5, x_scale_pos=x_scale_pos, x_scale_vals=x_scale_vals,
                                            auto_run=False)
    fc.get_special_coords_and_slopes()  # Step 1
    fc.set_init_y_blocks()
    fc.adjust_blocks_to_be_consistent_with_slopes()
    fc.trim_grid_to_target_dh()
    fc.build_req_y_node_positions()
    fc.set_x_nodes()
    fc.build_y_coords_grid_via_propagation()
    fc.adjust_for_smooth_surface()
    fc.set_soil_ids_to_vary_xy_grid()
    # fc.set_soil_ids_to_vary_y_grid()
    fc.create_mesh()

    # femesh = fc.femesh
    import o3plot
    import pyqtgraph as pg
    win = o3plot.create_scaled_window_for_tds(tds, title='build_y_coords_at_xcs')
    o3plot.plot_two_d_system(tds, win)
    o3plot.plot_finite_element_mesh(fc.femesh, win, start=False)
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

    for i in range(len(fc.sds)):
        win.plot(fc.sds[i][0], fc.sds[i][1], pen='b')
    win.plot([0, fc.tds.width], [-fc.tds.height, -fc.tds.height], pen='w')
    xns = fc.x_nodes
    for i in range(len(xns)):
        xc = xns[i]
        xn = xc * np.ones_like(fc.y_nodes[i])
        win.plot(xn, fc.y_nodes[i], pen=None, symbol='o', symbolPen=(200, 200, 200), symbolBrush=(200, 200, 200),
                 symbolSize=3)
    for i in range(len(fc.x_nodes2d)):
        xn = fc.x_nodes2d[i]
        win.plot(xn, fc.y_nodes[i], pen=None, symbol='o', symbolPen='r', symbolBrush='r', symbolSize=3)
    for i in range(len(fc.xcs_sorted)):
        win.addItem(pg.InfiniteLine(fc.xcs_sorted[i], angle=90, pen=(0, 255, 0, 100)))
    o3plot.show()


if __name__ == '__main__':
    # plot2()
    _example_simple_run()
    # _example_run()
    # replot()

