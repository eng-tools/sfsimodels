import numpy as np

from sfsimodels.exceptions import ModelError
from sfsimodels.models.abstract_models import PhysicalObject
from sfsimodels import checking_tools as ct


class Foundation(PhysicalObject):
    """
    An object to describe building foundations
    """
    _id = None
    name = None
    _width = None  # [m], The length of the foundation in the direction of shaking
    _length = None  # [m], The length of the foundation perpendicular to the shaking
    _depth = None  # [m], The depth of the foundation from the surface
    _height = None  # [m], The height of the foundation from base of foundation to ground floor
    _density = None  # [kg/m3], Density of foundation
    _mass = None  # kg
    ftype = None  # [], Foundation type

    inputs = [
        "name",
        "width",
        "length",
        "depth",
        "height",
        "density",
        "mass"
    ]

    def __str__(self):
        return "Foundation id: {0}, name: {1}".format(self.id, self.name)

    def __format__(self, format_spec):
        return "Foundation"

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    @property
    def area(self):
        try:
            return self.length * self.width
        except TypeError:
            return None

    @property
    def length(self):
        return self._length

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def mass(self):
        return self._mass

    @property
    def density(self):
        return self._density

    @property
    def weight(self):
        return self.mass * 9.8

    @length.setter
    def length(self, value):
        self._length = value

    @width.setter
    def width(self, value):
        self._width = value

    @height.setter
    def height(self, value):
        self._height = value

    @density.setter
    def density(self, value, override=False):
        density = self._calc_density()
        if density is not None and not ct.isclose(density, value) and not override:
            raise ModelError("Density inconsistent with set mass")
        self._density = value
        mass = self._calc_mass()
        if mass is not None and not ct.isclose(mass, self.mass):
            self.mass = mass

    @mass.setter
    def mass(self, value, override=False):
        mass = self._calc_mass()
        if mass is not None and not ct.isclose(mass, value) and not override:
            raise ModelError("Mass inconsistent with set density")
        self._mass = value
        density = self._calc_density()
        if density is not None and not ct.isclose(density, self.density):
            self.density = density

    def _calc_mass(self):
        try:
            return self.area * self.height * self.density
        except TypeError:
            return None

    def _calc_density(self):
        try:
            return self.mass / (self.area * self.height)
        except TypeError:
            return None
        except ZeroDivisionError:
            return None


class RaftFoundation(Foundation):
    """
    An extension to the Foundation Object to describe Raft foundations
    """
    ftype = "raft"

    def __str__(self):
        return "RaftFoundation id: {0}, name: {1}".format(self.id, self.name)

    @property
    def i_ww(self):
        return self.width * self.length ** 3 / 12

    @property
    def i_ll(self):
        return self.length * self.width ** 3 / 12

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
    pad_length = 1.0  # m  # TODO: make parameters protected
    pad_width = 1.0  # m

    def __str__(self):
        return "PadFoundation id: {0}, name: {1}".format(self.id, self.name)

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