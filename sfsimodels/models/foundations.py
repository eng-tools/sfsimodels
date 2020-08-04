from collections import OrderedDict

import numpy as np

from sfsimodels.exceptions import ModelError
from sfsimodels.models.abstract_models import PhysicalObject
from sfsimodels import checking_tools as ct
from sfsimodels.exceptions import deprecation


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
    base_type = "foundation"
    type = "foundation"
    _tolerance = 0.0001  # consistency tolerance
    _building = None
    x_bd = None
    z_bd = None

    _extra_class_inputs = [
        "id",
        "name",
        "base_type",
        "type",
        "width",
        "length",
        "depth",
        "height",
        "density",
        "mass",
        'x_bd',
        'z_bd'
    ]

    def __str__(self):
        return "Foundation id: {0}, name: {1}".format(self.id, self.name)

    def __format__(self, format_spec):
        return "Foundation"

    def __init__(self):
        super(Foundation, self).__init__()
        self.inputs = [
        "id",
        "name",
        "base_type",
        "type",
        "width",
        "length",
        "depth",
        "height",
        "density",
        "mass",
        'x_bd',
        'z_bd'
    ]

    @property
    def ancestor_types(self):
        return super(Foundation, self).ancestor_types + ["foundation"]

    @property
    def area(self):
        """Foundation area in plan"""
        try:
            return self.length * self.width
        except TypeError:
            return None

    @property
    def length(self):
        """Length of the foundation (typically in the out-of-plane direction)"""
        return self._length

    @property
    def width(self):
        """Length of the foundation (typically in the in-plane direction)"""
        return self._width

    @property
    def height(self):
        """Measure of the base of the foundation to the top"""
        return self._height

    @property
    def depth(self):
        """Measure of the base of the foundation to the surface of the soil"""
        return self._depth

    @property
    def mass(self):
        """The mass of the whole foundation"""
        return self._mass

    @property
    def density(self):
        """The mass density of the foundation [kg/m3]"""
        return self._density

    @property
    def weight(self):
        """The weight of the foundation [N]"""
        return self.mass * 9.8

    @length.setter
    def length(self, value):
        if value is None or value == "":
            return
        self._length = float(value)

    @width.setter
    def width(self, value):
        if value is None or value == "":
            return
        self._width = float(value)

    @height.setter
    def height(self, value):
        if value is None or value == "":
            return
        self._height = float(value)

    @depth.setter
    def depth(self, value):
        if value is None or value == "":
            return
        self._depth = float(value)

    def override_density(self, value):
        self._density = float(value)
        mass = self._calc_mass()
        if mass is not None and not ct.isclose(mass, self.mass):
            self.mass = mass

    @density.setter
    def density(self, value):
        if value is None or value == "":
            return
        density = self._calc_density()
        if density is not None and not np.isclose(density, value, rtol=self._tolerance):
            raise ModelError("Density inconsistent with set mass")
        self._density = float(value)
        mass = self._calc_mass()
        if mass is not None and not ct.isclose(mass, self.mass):
            self.mass = mass

    def override_mass(self, value):
        self._mass = float(value)
        density = self._calc_density()
        if density is not None and not ct.isclose(density, self.density, rel_tol=self._tolerance):
            self.density = density

    @mass.setter
    def mass(self, value):
        if value is None or value == "":
            return
        mass = self._calc_mass()
        if mass is not None and not ct.isclose(mass, value, rel_tol=self._tolerance):
            raise ModelError("Mass inconsistent with set density")
        self._mass = float(value)
        density = self._calc_density()
        if density is not None and not ct.isclose(density, self.density, rel_tol=self._tolerance):
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

    @property
    def building(self):
        return self._building

    def set_building(self, building, x=None, z=None, two_way=True):
        """
        Connect a building to the foundation at position (x, y)

        Parameters
        ----------
        building: sm.Building
        x: float
            Offset along x-axis of building centre line compared to foundation centre line
            (+ve is building to right of centre)
        z: float
            Offset along y-axis of building centre line compared to foundation centre line
            (+ve is building to right of centre)
        two_way: bool
            If true then also add the foundation to the building
        """

        if two_way:
            building.set_foundation(self, x=x, z=z, two_way=False)
        if x is not None:
            self.x_bd = float(x)
        if z is not None:
            self.z_bd = float(z)
        self._building = building


class StripFoundation(Foundation):
    """
    An extension to the Foundation Object to describe Strip foundations

    A strip foundation has an infinite length, so everything is computed for a unit length
    """
    ftype = "raft"
    type = "foundation_raft"
    _extra_class_inputs = []

    def __str__(self):
        return "FoundationRaft id: {0}, name: {1}".format(self.id, self.name)

    def __init__(self):
        super(StripFoundation, self).__init__()
        self.inputs = self.inputs + self._extra_class_inputs


class RaftFoundation(Foundation):
    """
    An extension to the Foundation Object to describe Raft foundations
    """
    ftype = "raft"
    type = "foundation_raft"
    _extra_class_inputs = []

    def __str__(self):
        return "FoundationRaft id: {0}, name: {1}".format(self.id, self.name)

    def __init__(self):
        super(RaftFoundation, self).__init__()
        self.inputs = self.inputs + self._extra_class_inputs

    @property
    def ancestor_types(self):
        return super(RaftFoundation, self).ancestor_types + ["foundation_raft"]

    @property
    def i_ww(self):
        """
        Contact moment-area around the width axis
        :return:
        """
        return self.width * self.length ** 3 / 12

    @property
    def i_ll(self):
        """
        Contact moment-area around the length axis
        :return:
        """
        return self.length * self.width ** 3 / 12


class PadFooting(Foundation):
    """
        An extension to the Foundation Object to describe Raft foundations
        """
    ftype = "pad_footing"
    type = "pad_footing"
    _extra_class_inputs = []

    def __str__(self):
        return "PadFooting id: {0}, name: {1}".format(self.id, self.name)

    def __init__(self):
        super(PadFooting, self).__init__()
        self.inputs = self.inputs + self._extra_class_inputs

    @property
    def ancestor_types(self):
        return super(PadFooting, self).ancestor_types + ["pad_footing"]

    @property
    def i_ww(self):
        """
        Contact moment-area around the width axis
        :return:
        """
        return self.width * self.length ** 3 / 12

    @property
    def i_ll(self):
        """
        Contact moment-area around the length axis
        :return:
        """
        return self.length * self.width ** 3 / 12


class PadFoundation(Foundation):
    """
    An extension to the Foundation Object to describe Pad foundations
    """
    ftype = "pad"
    type = "foundation_pad"
    n_pads_l = None  # Number of pads in length direction
    n_pads_w = None  # Number of pads in width direction
    _extra_class_inputs = [
        "n_pads_l",
        "n_pads_w",
        "pad_length",
        "pad_width",
    ]

    def __str__(self):
        return "PadFoundation id: {0}, name: {1}".format(self.id, self.name)

    def __init__(self):
        super(PadFoundation, self).__init__()
        self.inputs += self._extra_class_inputs
        self._pad = PadFooting()

    @property
    def ancestor_types(self):
        return super(PadFoundation, self).ancestor_types + ["foundation_pad"]

    @property
    def i_ww(self):
        """Second moment of inertia around the width axis."""
        d_values = []
        for i in range(self.n_pads_l):
            d_values.append(self.pad_position_l(i))
        d_values = np.array(d_values) - self.length / 2
        area_d_sqrd = sum(self.pad_area * d_values ** 2) * self.n_pads_w
        i_second = self.pad_i_ww * self.n_pads
        return area_d_sqrd + i_second

    @property
    def i_ll(self):
        """Second moment of inertia around the length axis."""
        d_values = []
        for i in range(self.n_pads_w):
            d_values.append(self.pad_position_w(i))
        d_values = np.array(d_values) - self.width / 2
        area_d_sqrd = sum(self.pad_area * d_values ** 2) * self.n_pads_l
        i_second = self.pad_i_ll * self.n_pads
        return area_d_sqrd + i_second

    @property
    def pad(self):
        return self._pad

    @pad.setter
    def pad(self, obj):
        self._pad = obj
        self._pad.depth = self.depth
        self._pad.height = self.height

    @property
    def pad_length(self):
        return self.pad.length

    @pad_length.setter
    def pad_length(self, value):
        self.pad.length = value

    @property
    def pad_width(self):
        return self.pad.width

    @pad_width.setter
    def pad_width(self, value):
        self.pad.width = value

    @property
    def n_pads(self):
        """Total number of pad footings"""
        return self.n_pads_w * self.n_pads_l

    @property
    def pad_area(self):
        """Area of a pad"""
        return self.pad_length * self.pad_width

    @property
    def pad_i_ww(self):
        """Second moment of inertia of a single pad around the width axis."""
        return self.pad_length ** 3 * self.pad_width / 12

    @property
    def pad_i_ll(self):
        """Second moment of inertia of a single pad around the length axis."""
        return self.pad_width ** 3 * self.pad_length / 12

    @property
    def area(self):
        """Contact area of the whole foundation in plan"""
        return self.n_pads * self.pad_area

    def pad_position_l(self, i):
        """
        Determines the position of the ith pad in the length direction.
        Assumes equally spaced pads.

        Parameters
        ----------
        i: int
            Ith number of pad in length direction (0-indexed)
        """
        if i >= self.n_pads_l:
            raise ModelError("pad index out-of-bounds")
        return (self.length - self.pad_length) / (self.n_pads_l - 1) * i + self.pad_length / 2

    def pad_position_w(self, i):
        """
        Determines the position of the ith pad in the width direction.
        Assumes equally spaced pads.

        Parameters
        ----------
        i: int
            Ith number of pad in width direction (0-indexed)
        """
        if i >= self.n_pads_w:
            raise ModelError("pad index out-of-bounds")
        return (self.width - self.pad_width) / (self.n_pads_w - 1) * i + self.pad_width / 2

    @property
    def height(self):
        """Measure of the base of the foundation to the top"""
        return self._height

    @height.setter
    def height(self, value):
        if value is None or value == "":
            return
        self._height = float(value)
        self._pad.height = float(value)

    @property
    def depth(self):
        """Measure of the base of the foundation to the surface of the soil"""
        return self._height

    @depth.setter
    def depth(self, value):
        if value is None or value == "":
            return
        self._depth = float(value)
        self._pad.depth = float(value)


class FoundationPad(PadFoundation):
    def __init__(self):
        deprecation("FoundationPad class is deprecated, use PadFoundation.")
        super(FoundationPad, self).__init__()


class FoundationRaft(RaftFoundation):
    def __init__(self):
        deprecation("Foundation class is deprecated, use RaftFoundation.")
        super(FoundationRaft, self).__init__()
