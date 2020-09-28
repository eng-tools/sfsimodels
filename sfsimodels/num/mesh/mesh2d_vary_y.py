import numpy as np
from sfsimodels.models.abstract_models import PhysicalObject
from sfsimodels.models.systems import TwoDSystem
from sfsimodels.functions import interp_left, interp2d


def remove_close_items(y, tol):
    diffs = np.diff(y)
    inds = np.where(diffs < tol)
    while len(inds[0]):  # progressively delete coordinate above until tolerance is reached
        if inds[0][0] == len(diffs) - 1:
            y = np.delete(y, inds[0][0])
        else:
            y = np.delete(y, inds[0][0] + 1)
        diffs = np.diff(y)
        inds = np.where(diffs < tol)
    return y


class FiniteElementVaryY2DMeshConstructor(object):  # maybe FiniteElementVertLine2DMesh
    x_act = None
    y_flat = None
    x_nodes = None
    y_nodes = None
    _soils = None
    x_index_to_sp_index = None
    _inactive_value = 1000000

    def __init__(self, tds, dy_target, x_scale_pos=None, x_scale_vals=None, dp: int = None, fd_eles=0, auto_run=True):
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
        fd_eles: int
            if =0 then elements corresponding to the foundation are removed, else provide element id
        """
        self.min_scale = 0.5
        self.max_scale = 2.0
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
        if auto_run:
            self.get_special_coords_and_slopes()  # Step 1
            self.set_init_y_blocks()
            self.adjust_blocks_to_be_consistent_with_slopes()
            self.trim_grid_to_target_dh()
            self.build_req_y_node_positions()
            self.build_y_coords_at_xcs()
            self.set_x_nodes()
            self.build_y_coords_grid()
            if self.dp is not None:
                self.set_to_decimal_places()
            self.set_soil_ids_to_grid()
            self.create_mesh()
            if not fd_eles:
                self.exclude_fd_eles()

    def get_special_coords_and_slopes(self):
        """Find the coordinates, layer boundaries and surface slopes that should be maintained in the FE mesh"""
        fd_coords = []
        x_off = 0.0
        yd = {}
        for i in range(len(self.tds.x_surf)):
            if self.tds.x_surf[i] <= self.tds.width:
                yd[self.tds.x_surf[i]] = []
        if self.tds.width not in yd:
            yd[self.tds.width] = []

        sds = []  # slope dict (stored left-to-right and bottom-to-top)
        for i in range(len(self.tds.bds)):
            x_bd = self.tds.x_bds[i]
            bd = self.tds.bds[i]
            fd_centre_x = x_bd + bd.x_fd
            y_surf = np.interp(fd_centre_x, self.tds.x_surf, self.tds.y_surf)
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
            sds.append([[x_left, x_right], [-bd.fd.depth + y_surf, -bd.fd.depth + y_surf]])

        for i in range(len(self.tds.sps)):
            x_curr = self.tds.x_sps[i]
            if i == len(self.tds.sps) - 1:
                x_next = self.tds.width
            else:
                x_next = self.tds.x_sps[i + 1] - x_off

            # get important x-coordinates that are between two soil profiles
            if x_curr not in yd:
                yd[x_curr] = []
            if x_next not in yd:
                yd[x_next] = []
            x_coords = np.array(list(yd))
            inds = np.where((x_coords >= x_curr) & (x_coords <= x_next))
            xs = np.sort(x_coords[inds])
            y_surf_at_xs = np.interp(xs, self.tds.x_surf, self.tds.y_surf)
            y_curr_surf = y_surf_at_xs[0]
            # Depths from defined soil profile
            int_yy = []
            angles = []
            for yy in range(1, self.tds.sps[i].n_layers + 1):
                # if self.tds.sps[i].layer_depth(yy) >= 0:
                int_yy.append(-self.tds.sps[i].layer_depth(yy) + y_curr_surf)
                angles.append(self.tds.sps[i].x_angles[yy-1])
            angles = np.array(angles)
            # angs = np.array(self.tds.sps[i].x_angles)[:-1]
            # angles = np.array(self.tds.sps[i].x_angles)[:-1]

            if xs[0] not in yd:
                yd[xs[0]] = []
            for j in range(len(xs) - 1):
                x0 = xs[j]
                x_next = xs[j]
                if x_next not in yd:
                    yd[x_next] = []
                x0_diff = x0 - x_curr
                xn_diff = x_next - x_curr
                if y_surf_at_xs[j] not in yd[x0]:
                    yd[x0].append(y_surf_at_xs[j])
                if y_surf_at_xs[j+1] not in yd[x_next]:
                    yd[x_next].append(y_surf_at_xs[j+1])
                for k in range(len(int_yy)):
                    y_curr = int_yy[k] + angles[k] * x0_diff
                    if y_curr < y_surf_at_xs[j] and y_curr not in yd[x0]:
                        yd[x0].append(y_curr)
                    y_next = int_yy[k] + angles[k] * xn_diff
                    if y_next < y_surf_at_xs[j+1] and y_next not in yd[x_next]:
                        yd[x_next].append(y_next)
                    if y_curr < y_surf_at_xs[j] and y_next < y_surf_at_xs[j+1]:
                        sds.append([[x0, x_next], [y_curr, y_next]])

            # x_diffs = xs - x_curr
            #
            # int_yy = np.array(int_yy)[1:]
            # if len(int_yy) == 0:
            #     continue
            # ys_curr = int_yy[:, np.newaxis] + angles[:, np.newaxis] * x_diffs[np.newaxis, :]
            # for j in range(len(xs)):
            #     yd[xs[j]] += list(ys_curr[:, j])
            # for j in range(len(xs) - 1):
            #     for k in range(len(ys_curr)):
            #         slope = [[xs[j], xs[j + 1]], [ys_curr[::-1][k][j], ys_curr[::-1][k][j + 1]]]
            #         sds.append(slope)

        for x in yd:
            yd[x].append(-self.tds.height)
            yd[x].append(np.interp(x, self.tds.x_surf, self.tds.y_surf))
            yd[x] = list(set(yd[x]))
            yd[x].sort()
        xcs = list(yd)
        xcs.sort()
        xcs = np.array(xcs)
        for i in range(len(xcs) - 1):
            xs = np.array([xcs[i], xcs[i + 1]])
            slope = [list(xs), list(np.interp(xs, self.tds.x_surf, self.tds.y_surf))]
            sds.append(slope)
        y_surf_max = max(self.tds.y_surf)

        # remove coordinates that are too close
        min_y = self.dy_target * self.min_scale
        tol = self.dy_target * self.min_scale
        for x in yd:
            yd[x] = remove_close_items(yd[x], tol=tol)
            diffs = np.diff(yd[x])
            inds = np.where(diffs < min_y - 0.00001)
            while len(inds[0]):
                yd[x][inds[0][0] + 1] = yd[x][inds[0][0]] + min_y
                yd[x] = remove_close_items(yd[x], tol=tol)
                diffs = np.diff(yd[x])
                inds = np.where(diffs < min_y - 0.00001)
        self.y_surf_at_xcs = {}
        for x in yd:
            self.y_surf_at_xcs[x] = yd[x][-1]
            if y_surf_max not in yd[x]:
                yd[x] = np.insert(yd[x], len(yd[x]), y_surf_max)
            yd[x] = np.array(yd[x])
        self.yd = yd
        x_act = list(self.yd)
        x_act.sort()
        self.xcs_sorted = np.array(x_act)
        self.sds = sds

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
        for pp in range(5):
            sds = self.sds
            for sd in sds:
                csum_y_blocks = [np.cumsum(self.y_blocks[xcs]) for xcs in self.y_blocks]
                x0 = sd[0][0]
                x1 = sd[0][1]
                y0 = sd[1][0]
                y1 = sd[1][1]
                ind_x0 = int(np.argmin(abs(xcs - x0)))
                ind_x1 = int(np.argmin(abs(xcs - x1)))
                ind_y0 = int(np.argmin(abs(np.array(yd_list[ind_x0]) - y0)))
                ind_y1 = int(np.argmin(abs(np.array(yd_list[ind_x1]) - y1)))
                x1_c = xcs[ind_x1]
                y1_c = yd_list[ind_x1][ind_y1]
                nb0 = csum_y_blocks[ind_x0][ind_y0 - 1]
                nb1 = csum_y_blocks[ind_x1][ind_y1 - 1]
                sgn = int(np.sign(y1 - y0))
                allowable_slope = 0.2
                dh_dzone = y1 - y0
                slope = dh_dzone / (x1 - x0)
                if abs(slope) < allowable_slope and nb0 == nb1:
                    continue
                diff_nb = nb1 - nb0

                while sgn != np.sign(diff_nb) and diff_nb != 0:
                    self.y_blocks[x1_c][ind_y1 - 1] += np.sign(diff_nb) * -1
                    nb1 += np.sign(diff_nb) * -1
                    if y1_c != self.y_surf_at_xcs[x1_c]:
                        self.y_blocks[x1_c][ind_y1] += np.sign(diff_nb) * 1
                    diff_nb = nb1 - nb0
                approx_grid_slope = (dh_dzone - diff_nb * self.dy_target) / (x1 - x0)
                if sgn != np.sign(approx_grid_slope):
                    pass  # this can be an issue if it cannot be adjusted
                if sgn * approx_grid_slope > allowable_slope:
                    nn = 0
                    while sgn * approx_grid_slope > allowable_slope:
                        nn += 1
                        # if no issues the adjust blocks
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
                    y1_below = yd_list[ind_x1][ind_y1 - 1]
                    if y1_c == self.y_surf_at_xcs[x1_c]:  # surface
                        y1_above = None
                    else:
                        y1_above = yd_list[ind_x1][ind_y1 + 1]
                    for nn in range(diff_nb):
                        diff_nb = nb1 - nb0
                        if diff_nb == 0:
                            break
                        nb_sgn = np.sign(diff_nb)
                        approx_new_slope = (dh_dzone - (diff_nb - nb_sgn * (nn + 1)) * self.dy_target) / (x1 - x0)
                        if sgn * approx_new_slope > allowable_slope:
                            break
                        nb_below = self.y_blocks[x1_c][ind_y1 - 1]
                        new_nb_below = nb_below + nb_sgn * -1
                        use_2_below = False
                        if new_nb_below == 0:  # try bring from even lower layer
                            nb_2_below = self.y_blocks[x1_c][ind_y1 - 2]
                            new_nb_2_below = nb_2_below + nb_sgn * -1
                            y1_2_below = yd_list[ind_x1][ind_y1 - 2]
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
                            new_dh_above = (y1_above - y1_c) / (nb_above + nb_sgn * 1)
                            if not (min_dh < new_dh_above < max_dh):
                                break
                        # if no issues the adjust blocks
                        if use_2_below:
                            self.y_blocks[x1_c][ind_y1 - 2] += nb_sgn * -1
                        else:
                            self.y_blocks[x1_c][ind_y1 - 1] += nb_sgn * -1
                        nb1 += nb_sgn * -1
                        if y1_above is not None:
                            self.y_blocks[x1_c][ind_y1] += nb_sgn * 1

        # Step 5: Set the total number of blocks to be equal to the minimum number of blocks used in the highest columns
        h_max = max(self.tds.y_surf)
        n_blocks = np.array([sum(self.y_blocks[xc]) for xc in xcs])
        inds = np.where(np.interp(xcs, self.tds.x_surf, self.tds.y_surf) == h_max)[0]
        n_max = min(n_blocks[inds])  # minimum number of blocks at top
        # create null nodes
        for i in range(len(xcs)):
            x0 = xcs[i]
            if n_blocks[i] != n_max:
                n_extra = n_max - n_blocks[i]
                self.y_blocks[x0][-1] += n_extra

    def trim_grid_to_target_dh(self):
        """Check mesh for potential thin layers and try to remove rows of elements to get elements close to target dh"""
        xcs = self.xcs_sorted
        # try to trim mesh to be closer to target dh
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
                    if (i, j) in opts_tried:
                        av_dhs[i].append(1000)
                        continue
                    nb = y_node_nums_at_xcs[i][j + 1] - y_node_nums_at_xcs[i][j]
                    av_dhs[i].append((y_coords_at_xcs[i][j + 1] - y_coords_at_xcs[i][j]) / nb)

                min_dhs.append(min(av_dhs[i]))
            if min(min_dhs) < self.dy_target:
                x_ind = min_dhs.index(min(min_dhs))
                y_ind = av_dhs[x_ind].index(min_dhs[x_ind])
                nb_lowest = y_node_nums_at_xcs[x_ind][y_ind]  # range where element could be removed
                nb_highest = y_node_nums_at_xcs[x_ind][y_ind + 1]
                hzone = y_coords_at_xcs[x_ind][y_ind + 1] - y_coords_at_xcs[x_ind][y_ind]
                max_new_dh = hzone / (nb_highest - nb_lowest - 1)
                for w in range(len(y_node_nums_at_xcs)):
                    y_ind = interp_left(nb_lowest, y_node_nums_at_xcs[w])
                    nb_low = y_node_nums_at_xcs[w][y_ind]
                    nb_high = y_node_nums_at_xcs[w][y_ind + 1]
                    hzone = y_coords_at_xcs[w][y_ind + 1] - y_coords_at_xcs[w][y_ind]
                    if nb_highest > nb_high:
                        nb_highest = nb_high
                    new_dh = hzone / (nb_high - nb_low - 1)
                    if max_new_dh < new_dh:
                        max_new_dh = new_dh
                if max_new_dh < self.dy_target * self.max_scale * 0.7:
                    for w in range(len(y_node_nums_at_xcs)):
                        y_ind = interp_left(nb_lowest, y_node_nums_at_xcs[w])
                        self.y_blocks[xcs[w]][y_ind] -= 1
                        # for k in range(y_ind + 1, len(y_node_nums_at_xcs[w])):
                        #     y_node_nums_at_xcs[w][k] -= 1
                else:
                    opts_tried.append((x_ind, y_ind))
            else:
                break

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
        sds = self.sds
        for sd in sds:
            x0 = sd[0][0]
            x1 = sd[0][1]
            y0 = sd[1][0]
            y1 = sd[1][1]
            ind_x0 = int(np.argmin(abs(xcs - x0)))
            ind_x1 = int(np.argmin(abs(xcs - x1)))
            ind_y0 = int(np.argmin(abs(np.array(req_y_coords_at_xcs[ind_x0]) - y0)))
            ind_y1 = int(np.argmin(abs(np.array(req_y_coords_at_xcs[ind_x1]) - y1)))
            y0_c = req_y_coords_at_xcs[ind_x0][ind_y0]
            nb0 = y_node_nums_at_xcs[ind_x0][ind_y0]
            nb1 = y_node_nums_at_xcs[ind_x1][ind_y1]
            if nb0 != nb1:
                diff_nb = nb1 - nb0
                new_nb = y_node_nums_at_xcs[ind_x1][ind_y1] - diff_nb
                if new_nb not in y_node_nums_at_xcs[ind_x1]:
                    dh_upper = (req_y_coords_at_xcs[ind_x1][ind_y1] - y0_c) / diff_nb
                    if ind_y1 - 2 < 0:
                        nb_lower = nb1 - diff_nb
                    else:
                        nb_lower = nb1 - y_node_nums_at_xcs[ind_x1][ind_y1 - 1] - diff_nb
                    dh_lower = (y0_c - req_y_coords_at_xcs[ind_x1][ind_y1 - 1]) / nb_lower
                    if min_dh < dh_upper < max_dh and min_dh < dh_lower < max_dh:
                        y_node_nums_at_xcs[ind_x1].append(new_nb)
                        y_node_nums_at_xcs[ind_x1].sort()
                        req_y_coords_at_xcs[ind_x1].append(y0_c)
                        req_y_coords_at_xcs[ind_x1].sort()

        # Step 3: Build node number lists
        req_y_nodes = []
        for i, xc0 in enumerate(xcs):
            req_y_nodes.append(list(np.array(y_node_nums_at_xcs[i]) + 1))
            req_y_nodes[i][0] = 0
        self.req_y_nodes = req_y_nodes
        self.req_y_coords_at_xcs = req_y_coords_at_xcs

    def build_y_coords_at_xcs(self):
        """Creates the y-coordinates for each node along each significant vertical line"""
        xcs = self.xcs_sorted
        req_y_nodes = self.req_y_nodes
        y_coords_at_xcs = self.req_y_coords_at_xcs
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
                    if y_nodes[i-1][j] >= self.y_surf_at_xcs[xcs[i-1]]:
                        yys = np.interp(np.arange(j, req_y_nodes[i][-1] + 1), req_y_nodes[i], y_coords_at_xcs[i])
                        new_y_vals += list(yys)
                        break
                    else:
                        # get next and previous req points and check the slope of each of the those back to left col
                        ind_below = interp_left(j, req_y_nodes[i])
                        req_n_below = req_y_nodes[i][ind_below]
                        req_n_above = req_y_nodes[i][ind_below + 1]
                        # sf is slope below plus slope above times j / (ind_above - ind_below)
                        dh_dzone_below = y_coords_at_xcs[i][ind_below] - y_nodes[i-1][req_n_below]
                        dh_dzone_above = y_coords_at_xcs[i][ind_below + 1] - y_nodes[i - 1][req_n_above]
                        dh = dh_dzone_below + (dh_dzone_above - dh_dzone_below) / (req_n_above - req_n_below) * (j - req_n_below)
                        new_y_vals.append(y_nodes[i-1][j] + dh)
                else:
                    ind = req_y_nodes[i].index(j)
                    new_y_vals.append(y_coords_at_xcs[i][ind])
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
            assert diff_nb > 0  # currently only supports smoothing forward
            next_slope = surf_at_next_xc - surf_at_xc
            # trim either half the block or min_dh
            if next_slope > 0:
                next_ys = y_nodes[i+1][ind_yc+1: ind_nc + 1]
                # y_nodes[i][ind_yc: ind_nc] = (next_ys - next_ys[0]) * 0.5 + next_ys[0]
                y_nodes[i][ind_yc+1: ind_nc + 1] = next_ys

        self.y_coords_at_xcs = y_nodes[:, ::-1]  # invert y-values

    def build_y_coords_grid(self):
        """Interpolates the position of all nodes based on the coordinates of the significant lines"""
        self.y_nodes = interp2d(self.x_nodes, np.array(self.xcs_sorted), self.y_coords_at_xcs)

    def set_x_nodes(self):
        """Determine optimal position of node x-coordinates"""
        dxs = [0]
        for xx in range(1, len(self.xcs_sorted)):
            x_shift = self.xcs_sorted[xx] - self.xcs_sorted[xx - 1]
            x_incs = np.linspace(self.xcs_sorted[xx - 1], self.xcs_sorted[xx], 20)
            scale = interp_left(x_incs, self.x_scale_pos, self.x_scale_vals)
            av_scale = np.mean(scale)
            av_size = av_scale * self.dy_target
            n_x_eles = int(x_shift / av_size + 0.99)
            av_ele_width = x_shift / n_x_eles
            x_start = self.xcs_sorted[xx - 1]
            x_incs = []
            for n in range(n_x_eles):
                prox_x_inc = interp_left([x_start], self.x_scale_pos, self.x_scale_vals)[0] * self.dy_target
                x_temp_points = np.linspace(x_start, x_start + prox_x_inc, 5)
                curr_scale = np.mean(interp_left(x_temp_points, self.x_scale_pos, self.x_scale_vals))
                x_inc = curr_scale / av_scale * av_ele_width
                x_incs.append(x_inc)
                x_start += x_inc
            # assert x_start == self.x_act[xx], (x_start, self.x_act[xx])
            # assert np.isclose(x_start, self.x_act[xx]), (x_start, self.x_act[xx])
            x_incs = np.array(x_incs) * x_shift / sum(x_incs)
            dxs += list(x_incs)

        self.x_nodes = np.cumsum(dxs)

    @property
    def soils(self):
        return self._soils

    def set_to_decimal_places(self):
        """Adjusts the node coordinates to a certain number of decimal places"""
        self.y_nodes = np.round(self.y_nodes, self.dp)
        self.x_nodes = np.round(self.x_nodes, self.dp)

    def set_soil_ids_to_grid(self):
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
                x_angles = [0] + list(sp.x_angles)
                sp_x = self.tds.x_sps[pid]
                for ll in range(1, sp.n_layers + 1):
                    yc = y_centres[xx][yy]
                    if -y_centres[xx][yy] > (sp.layer_depth(ll) - x_angles[ll - 1] * (x_centres[xx] - sp_x) - self.y_surf_at_sps[pid]):
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

    def create_mesh(self):
        self.femesh = FiniteElementVaryY2DMesh(self.x_nodes, self.y_nodes, self.soil_grid, self.soils)

    def exclude_fd_eles(self):
        for i, bd in enumerate(self.tds.bds):
            fd = bd.fd
            fcx = self.tds.x_bds[i] + bd.x_fd
            fcy = np.interp(fcx, self.tds.x_surf, self.tds.y_surf)
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
    type = 'vary_2d'

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
    fc = FiniteElementVaryY2DMeshConstructor(tds, 0.3, x_scale_pos=x_scale_pos, x_scale_vals=x_scale_vals)
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
    sp.x_angles = [0.05, 0.0]
    sp2.x_angles = [0.0, 0.0]
    tds = TwoDSystem(width=25, height=10)
    tds.add_sp(sp, x=0)
    tds.add_sp(sp2, x=14)
    tds.x_surf = np.array([0, 10, 12, 25])
    tds.y_surf = np.array([0, 0, 2, 2.3])

    x_scale_pos = np.array([0, 5, 15, 30])
    x_scale_vals = np.array([2., 1.0, 2.0, 3.0])
    fc = FiniteElementVaryY2DMeshConstructor(tds, 0.5, x_scale_pos=x_scale_pos, x_scale_vals=x_scale_vals)
    femesh = fc.femesh
    # show = 1
    # if show:
    #     show_constructor(fc)



if __name__ == '__main__':
    # plot2()
    # _example_simple_run()
    _example_run()
    # replot()
