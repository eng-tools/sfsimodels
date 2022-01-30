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
    _ip_axis = None
    _mass_density = None  # [kg/m3], Density of foundation
    _mass = None  # kg
    base_type = "foundation"
    type = "foundation"
    _tolerance = 0.0001  # consistency tolerance
    _building = None
    x_bd = None
    z_bd = None
    ip_axis = None
    oop_axis = None

    _extra_class_inputs = [
        "id",
        "name",
        "base_type",
        "type",
        "width",
        "length",
        "depth",
        "height",
        "mass_density",
        "mass",
        'x_bd',
        'z_bd',
        'ip_axis'
    ]

    def __str__(self):
        return "Foundation id: {0}, name: {1}".format(self.id, self.name)

    def __format__(self, format_spec):
        return "Foundation"

    def __init__(self, **kwargs):
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
        "mass_density",
        "mass",
        'x_bd',
        'z_bd',
        'ip_axis'
        ]
        self.stack = []
        for item in  kwargs:
            self.__setattr__(item, kwargs[item])
            self.stack.append(item)

    @property
    def ancestor_types(self):
        return super(Foundation, self).ancestor_types + ["foundation"]

    def get_oop_axis(self, ip_axis):
        # deprecated
        if ip_axis == 'length':
            return 'width'
        elif ip_axis == 'width':
            return 'length'
        return None
    
    @property
    def lip(self):
        ax = self.ip_axis
        if ax is None:
            return None
        return getattr(self, ax)

    @property
    def loop(self):
        ax = self.oop_axis
        if ax is None:
            return None
        return getattr(self, ax)

    @property
    def lshort(self):
        return min(self.length, self.width)

    @property
    def llong(self):
        return max(self.length, self.width)

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
        return self._mass_density

    @property
    def mass_density(self):
        """The mass density of the foundation [kg/m3]"""
        return self._mass_density

    @property
    def weight(self):
        """The weight of the foundation [N]"""
        return self.mass * 9.8

    @length.setter
    def length(self, value):
        if value is None or value == "":
            return
        self._length = float(value)
        self._add_to_stack('length', float(value))

    @width.setter
    def width(self, value):
        if value is None or value == "":
            return
        self._width = float(value)
        self._add_to_stack('width', float(value))

    @height.setter
    def height(self, value):
        if value is None or value == "":
            return
        self._height = float(value)
        self._add_to_stack('height', float(value))

    @depth.setter
    def depth(self, value):
        if value is None or value == "":
            return
        self._depth = float(value)
        self._add_to_stack('depth', float(value))

    def override_density(self, value):
        self._density = float(value)
        mass = self._calc_mass()
        if mass is not None and not ct.isclose(mass, self.mass):
            self.mass = mass

    @density.setter
    def density(self, value):
        self.mass_density = value

    @mass_density.setter
    def mass_density(self, value):
        if value is None or value == "":
            return
        density = self._calc_mass_density()
        if density is not None and not np.isclose(density, value, rtol=self._tolerance):
            raise ModelError("Density inconsistent with set mass")
        self._mass_density = float(value)
        self._add_to_stack('mass_density', float(value))
        mass = self._calc_mass()
        if mass is not None and not ct.isclose(mass, self.mass):
            self.mass = mass

    def override_mass(self, value):
        self._mass = float(value)
        density = self._calc_mass_density()
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
        self._add_to_stack('mass', self._mass)
        density = self._calc_mass_density()
        if density is not None and not ct.isclose(density, self.density, rel_tol=self._tolerance):
            self.mass_density = density

    def _calc_mass(self):
        try:
            return self.area * self.height * self.density
        except TypeError:
            return None

    def _calc_mass_density(self):
        try:
            return self.mass / (self.area * self.height)
        except TypeError:
            return None
        except ZeroDivisionError:
            return None

    @property
    def ip_axis(self):
        return self._ip_axis

    @ip_axis.setter
    def ip_axis(self, ip_axis):
        if ip_axis is None or ip_axis == '':
            self._ip_axis = None
            self._oop_axis = None
            return
        elif ip_axis == 'width':
            self._oop_axis = 'length'
        elif ip_axis == 'length':
            self._oop_axis = 'width'
        else:
            raise ModelError("ip_axis must be either 'width', 'length' or None")
        self._ip_axis = ip_axis
        self._add_to_stack('ip_axis', ip_axis)

    @property
    def oop_axis(self):
        return self._oop_axis

    @oop_axis.setter
    def oop_axis(self, oop_axis):
        if oop_axis is None:
            self._ip_axis = None
            self._oop_axis = None
            return
        elif oop_axis == 'width':
            self._ip_axis = 'length'
        elif oop_axis == 'length':
            self._ip_axis = 'width'
        else:
            raise ModelError("oop_axis must be either 'width', 'length' or None")
        self._oop_axis = oop_axis
        self._add_to_stack('oop_axis', oop_axis)

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

    def reset_all(self):
        """
        Resets all parameters to None
        """
        for item in self.inputs:
            setattr(self, "_%s" % item, None)
        self.stack = []

    def _add_to_stack(self, item, value):
        """
        Add a parameter-value pair to the stack of parameters that have been set.
        :param item:
        :param value:
        :return:
        """
        p_value = (item, value)
        if p_value not in self.stack:
            self.stack.append(p_value)

    def override(self, item, value):
        """
        Can set a parameter to a value that is inconsistent with existing values.

        This method sets the inconsistent value and then reapplies all existing values
        that are still consistent, all non-consistent (conflicting) values are removed from the object
        and returned as a list

        :param item: name of parameter to be set
        :param value: value of the parameter to be set
        :return: list, conflicting values
        """
        if not hasattr(self, item):
            raise KeyError("Soil Object does not have property: %s", item)
        try:
            setattr(self, item, value)  # try to set using normal setter method
            return []
        except ModelError:
            pass  # if inconsistency, then need to rebuild stack
        # create a new temporary stack
        temp_stack = list(self.stack)
        # remove item from original position in stack
        temp_stack[:] = (value for value in temp_stack if value[0] != item)
        # add item to the start of the stack
        temp_stack.insert(0, (item, value))
        # clear object, ready to rebuild
        self.reset_all()
        # reapply trace, one item at a time, if conflict then don't add the conflict.
        conflicts = []
        for item, value in temp_stack:
            # catch all conflicts
            try:
                setattr(self, item, value)
                if item in ['gravity']:
                    self._add_to_stack(item, value)
            except ModelError:
                conflicts.append(item)
        return conflicts


class StripFoundation(Foundation):
    """
    An extension to the Foundation Object to describe Strip foundations

    A strip foundation has an infinite length, so everything is computed for a unit length
    """
    ftype = "raft"
    # type = "foundation_raft"
    type = "strip_foundation"
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
    # type = "foundation_raft"
    type = "raft_foundation"
    _extra_class_inputs = []

    def __str__(self):
        return "FoundationRaft id: {0}, name: {1}".format(self.id, self.name)

    def __init__(self, **kwargs):
        super(RaftFoundation, self).__init__(**kwargs)
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
        An extension to the Foundation Object to describe Pad Footings which are members of PadFoundations
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
    # type = "foundation_pad"
    type = "pad_foundation"
    n_pads_l = None  # Number of pads in length direction
    n_pads_w = None  # Number of pads in width direction
    _extra_class_inputs = [
        "n_pads_l",
        "n_pads_w",
        "pad_length",
        "pad_width",
        "tie_beam_sect_in_width_dir",
        "tie_beam_sect_in_length_dir",
        "pad_pos_in_length_dir",
        "pad_pos_in_width_dir"
    ]
    loading_pre_reqs = ('beam_column_element',)

    def __str__(self):
        return "PadFoundation id: {0}, name: {1}".format(self.id, self.name)

    def __init__(self):
        super(PadFoundation, self).__init__()
        self.inputs += self._extra_class_inputs
        self._pad = PadFooting()
        # self._tie_beam_sect_in_width_dir = None  # Should be a section object
        # self._tie_beam_sect_in_length_dir = None
        self._tie_beam_in_width_dir = None  # Should be a element object
        self._tie_beam_in_length_dir = None
        self._pad_pos_in_length_dir = None
        self._pad_pos_in_width_dir = None
        self.skip_list = list(self.skip_list) + ["tie_beam_sect_in_width_dir",
                           "tie_beam_sect_in_length_dir"]

    def add_to_dict(self, models_dict, return_mdict=False, **kwargs):
        if self.base_type not in models_dict:
            models_dict[self.base_type] = OrderedDict()
        mdict = self.to_dict(**kwargs)
        if self.tie_beam_in_length_dir is not None:
            self.tie_beam_in_length_dir.add_to_dict(models_dict, **kwargs)
            if self.tie_beam_in_length_dir.id is None:
                self.tie_beam_in_length_dir.id = 1
            mdict['tie_beam_in_length_dir'] = {'beam_column_element_id': self.tie_beam_in_length_dir.id,
            'beam_column_element_unique_hash': self.tie_beam_in_length_dir.unique_hash}

        if return_mdict:
            return mdict
        models_dict[self.base_type][self.unique_hash] = mdict

    @property
    def ancestor_types(self):
        return super(PadFoundation, self).ancestor_types + ["foundation_pad"]

    @property
    def i_ww(self):
        """Second moment of inertia around the width axis."""
        d_values = []
        for i in range(self.n_pads_l):
            d_values.append(self.get_pad_pos_in_length_dir(i))
        d_values = np.array(d_values) - self.length / 2
        area_d_sqrd = sum(self.pad_area * d_values ** 2) * self.n_pads_w
        i_second = self.pad_i_ww * self.n_pads
        return area_d_sqrd + i_second

    @property
    def i_ll(self):
        """Second moment of inertia around the length axis."""
        d_values = []
        for i in range(self.n_pads_w):
            d_values.append(self.get_pad_pos_in_width_dir(i))
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

    def get_pad_pos_in_length_dir(self, i):
        """
        Determines the centre position of the ith pad in the length direction.

        Parameters
        ----------
        i: int
            Ith number of pad in length direction (0-indexed)
        """
        if i >= self.n_pads_l:
            raise ModelError("pad index out-of-bounds")
        if self._pad_pos_in_length_dir is None:
            raise ModelError('pad positions not set')

        return self._pad_pos_in_length_dir[i]

    def set_pad_pos_in_length_dir_as_equally_spaced(self):
        """
        Sets the centre position of the pad footings in length direction

        Assumes equally spaced pads and that pad outer edges give the foundation length.

        Returns
        -------

        """
        xs = np.arange(self.n_pads_l)
        if self.n_pads_l == 1:
            self._pad_pos_in_length_dir = np.array([self.length / 2])
            return
        self._pad_pos_in_length_dir = (self.length - self.pad_length) / (self.n_pads_l - 1) * xs + self.pad_length / 2

    @property
    def pad_pos_in_length_dir(self):
        return self._pad_pos_in_length_dir

    @pad_pos_in_length_dir.setter
    def pad_pos_in_length_dir(self, values):
        if values is None:
            self._pad_pos_in_length_dir = values
            return
        if self.n_pads_l is not None:
            assert len(values) == self.n_pads_l
        else:
            self.n_pads_l = len(values)
        self._pad_pos_in_length_dir = values

    def pad_position_l(self, i):
        deprecation('pad_position_l has deprecated - use get_pad_pos_in_length_dir')
        return self.get_pad_pos_in_length_dir(i)

    def get_pad_pos_in_width_dir(self, i):
        """
        Determines the centre position of the ith pad in the width direction.

        Parameters
        ----------
        i: int
            Ith number of pad in width direction (0-indexed)
        """
        if i >= self.n_pads_w:
            raise ModelError("pad index out-of-bounds")
        if self._pad_pos_in_width_dir is None:
            raise ModelError('pad positions not set')

        return self._pad_pos_in_width_dir[i]

    def set_pad_pos_in_width_dir_as_equally_spaced(self):
        """
        Sets the centre position of the pad footings in width direction

        Assumes equally spaced pads and that pad outer edges give the foundation width.

        Returns
        -------

        """
        xs = np.arange(self.n_pads_w)
        if self.n_pads_w == 1:
            self._pad_pos_in_width_dir = np.array([self.width / 2])
            return
        self._pad_pos_in_width_dir = (self.width - self.pad_width) / (self.n_pads_w - 1) * xs + self.pad_width / 2

    @property
    def pad_pos_in_width_dir(self):
        return self._pad_pos_in_width_dir

    @pad_pos_in_width_dir.setter
    def pad_pos_in_width_dir(self, values):
        if values is None:
            self._pad_pos_in_width_dir = values
            return
        if self.n_pads_w is not None:
            assert len(values) == self.n_pads_w
        else:
            self.n_pads_w = len(values)
        self._pad_pos_in_width_dir = values

    def pad_position_w(self, i):
        deprecation('pad_position_w has deprecated - use get_pad_pos_in_width_dir')
        return self.get_pad_pos_in_width_dir(i)

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
        return self._depth

    @depth.setter
    def depth(self, value):
        if value is None or value == "":
            return
        self._depth = float(value)
        self._pad.depth = float(value)

    # @property
    # def tie_beam_sect_in_width_dir(self):
    #     return self._tie_beam_sect_in_width_dir
    #
    # @tie_beam_sect_in_width_dir.setter
    # def tie_beam_sect_in_width_dir(self, value):
    #     self._tie_beam_sect_in_width_dir = value
    #
    # @property
    # def tie_beam_sect_in_length_dir(self):
    #     return self._tie_beam_sect_in_length_dir
    #
    # @tie_beam_sect_in_length_dir.setter
    # def tie_beam_sect_in_length_dir(self, value):
    #     self._tie_beam_sect_in_length_dir = value

    @property
    def tie_beam_in_width_dir(self):
        return self._tie_beam_in_width_dir

    @tie_beam_in_width_dir.setter
    def tie_beam_in_width_dir(self, value):
        if isinstance(value, list):  # need to unpack from ecp file
            self._tie_beam_in_width_dir = value[0]
        self._tie_beam_in_width_dir = value

    @property
    def tie_beam_in_length_dir(self):
        return self._tie_beam_in_length_dir

    @tie_beam_in_length_dir.setter
    def tie_beam_in_length_dir(self, value):
        if isinstance(value, list):  # need to unpack from ecp file
            self._tie_beam_in_length_dir = value[0]
        self._tie_beam_in_length_dir = value


class FoundationPad(PadFoundation):
    def __init__(self):
        deprecation("FoundationPad class is deprecated, use PadFoundation.")
        super(FoundationPad, self).__init__()


class FoundationRaft(RaftFoundation):
    def __init__(self):
        deprecation("Foundation class is deprecated, use RaftFoundation.")
        super(FoundationRaft, self).__init__()
