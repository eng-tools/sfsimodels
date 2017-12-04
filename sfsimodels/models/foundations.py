import numpy as np

from sfsimodels.exceptions import ModelError
from sfsimodels.models.abstract_models import PhysicalObject


class Foundation(PhysicalObject):
    """
    An object to describe building foundations
    """
    width = 0.0  # [m], The length of the foundation in the direction of shaking
    length = 0.0  # [m], The length of the foundation perpendicular to the shaking
    depth = 0.0  # [m], The depth of the foundation from the surface
    height = 0.0  # [m], The height of the foundation from base of foundation to ground floor
    density = 0.0  # [kg/m3], Density of foundation
    weight = 0.0  # [kN]
    ftype = None  # [], Foundation type

    inputs = [
        "width",
        "length",
        "depth",
        "height",
        "density"
    ]

    @property
    def area(self):
        return self.length * self.width

    @property
    def mass(self):
        return self.area * self.height * self.density


class RaftFoundation(Foundation):
    """
    An extension to the Foundation Object to describe Raft foundations
    """
    ftype = "raft"

    @property
    def i_ww(self):
        return self.width * self.length ** 3 / 12

    @property
    def i_ll(self):
        return self.length * self.width ** 3 / 12

    @property
    def mass(self):
        return self.area * self.height * self.density

    @property
    def weight(self):
        return self.mass * 9.8

    @property
    def inputs(self):
        input_list = super(RaftFoundation, self).inputs
        new_inputs = [
            "i_ww",
            "i_ll"
        ]
        return input_list + new_inputs


class PadFoundation(Foundation):
    """
    An extension to the Foundation Object to describe Pad foundations
    """
    ftype = "pad"
    n_pads_l = 4  # Number of pads in length direction
    n_pads_w = 3  # Number of pads in width direction
    pad_length = 1.0  # m
    pad_width = 1.0  # m

    @property
    def i_ww(self):
        """
        Second moment of inertia around the width axis.
        :return:
        """
        d_values = []
        for i in range(self.n_pads_l):
            d_values.append(self.pad_position_l(i))
        d_values = np.array(d_values) - self.length / 2
        area_d_sqrd = sum(self.pad_area * d_values ** 2) * self.n_pads_w
        i_second = self.pad_i_ww * self.n_pads
        return area_d_sqrd + i_second

    @property
    def i_ll(self):
        d_values = []
        for i in range(self.n_pads_w):
            d_values.append(self.pad_position_w(i))
        d_values = np.array(d_values) - self.width / 2
        area_d_sqrd = sum(self.pad_area * d_values ** 2) * self.n_pads_l
        i_second = self.pad_i_ll * self.n_pads
        return area_d_sqrd + i_second

    @property
    def n_pads(self):
        return self.n_pads_w * self.n_pads_l

    @property
    def pad_area(self):
        return self.pad_length * self.pad_width

    @property
    def pad_i_ww(self):
        return self.pad_length ** 3 * self.pad_width / 12

    @property
    def pad_i_ll(self):
        return self.pad_width ** 3 * self.pad_length / 12

    @property
    def area(self):
        return self.n_pads * self.pad_area

    @property
    def weight(self):
        return self.mass * 9.8

    @property
    def inputs(self):
        input_list = super(PadFoundation, self).inputs
        new_inputs = [
            "i_ww",
            "i_ll"
        ]
        return input_list + new_inputs

    def pad_position_l(self, i):
        """
        Determines the position of the ith pad in the length direction.
        Assumes equally spaced pads.
        :param i: ith number of pad in length direction (0-indexed)
        :return:
        """
        if i >= self.n_pads_l:
            raise ModelError("pad index out-of-bounds")
        return (self.length - self.pad_length) / (self.n_pads_l - 1) * i + self.pad_length / 2

    def pad_position_w(self, i):
        """
        Determines the position of the ith pad in the width direction.
        Assumes equally spaced pads.
        :param i: ith number of pad in width direction (0-indexed)
        :return:
        """
        if i >= self.n_pads_w:
            raise ModelError("pad index out-of-bounds")
        return (self.width - self.pad_width) / (self.n_pads_w - 1) * i + self.pad_width / 2