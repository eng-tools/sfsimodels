import numpy as np

import math
from sfsimodels.models.abstract_models import PhysicalObject
from sfsimodels.models import Hazard, Foundation, Soil
from sfsimodels.models.material import Concrete


class Building(PhysicalObject):
    """
    An object to define Buildings
    """
    physical_type = "building"
    _floor_length = None
    _floor_width = None
    _interstorey_heights = np.array([0.0])  # m
    _storey_masses = np.array([0.0])  # kg
    _concrete = Concrete()
    g = 9.81  # m/s2  # gravity

    inputs = [
        'floor_length',
        'floor_width',
        'interstorey_heights',
        'n_storeys'
    ]

    @property
    def floor_length(self):
        return self._floor_length

    @floor_length.setter
    def floor_length(self, value):
        self._floor_length = value

    @property
    def floor_width(self):
        return self._floor_width

    @floor_width.setter
    def floor_width(self, value):
        self._floor_width = value

    @property
    def concrete(self):
        return self._concrete

    @concrete.setter
    def concrete(self, conc_inst):
        self._concrete = conc_inst

    @property
    def floor_area(self):
        try:
            return self.floor_length * self.floor_width
        except TypeError:
            return None

    @property
    def heights(self):
        return np.cumsum(self._interstorey_heights)

    @property
    def max_height(self):
        return np.sum(self._interstorey_heights)

    @property
    def n_storeys(self):
        return len(self._interstorey_heights)

    @property
    def interstorey_heights(self):
        return self._interstorey_heights

    @interstorey_heights.setter
    def interstorey_heights(self, heights):
        self._interstorey_heights = np.array(heights)

    @property
    def storey_masses(self):
        return self._storey_masses

    @storey_masses.setter
    def storey_masses(self, masses):
        self._storey_masses = np.array(masses)

    def set_storey_masses_by_stresses(self, stresses):
        self.storey_masses = stresses * self.floor_area / 9.8


class FrameBuilding(Building):
    _bay_lengths = np.array([])  # protected
    _beam_depths = np.array([])  # protected
    _n_seismic_frames = None
    _n_gravity_frames = None

    @property
    def inputs(self):
        input_list = super(FrameBuilding, self).inputs
        new_inputs = [
            "bay_lengths",
            "beam_depths",
            "n_seismic_frames",
            "n_gravity_frames"
        ]
        return input_list + new_inputs


    @property
    def beam_depths(self):
        return self._beam_depths

    @beam_depths.setter
    def beam_depths(self, beam_depths):
        self._beam_depths = np.array(beam_depths)

    @property
    def bay_lengths(self):
        return self._bay_lengths

    @bay_lengths.setter
    def bay_lengths(self, bay_lengths):
        self._bay_lengths = np.array(bay_lengths)

    @property
    def n_seismic_frames(self):
        return self._n_seismic_frames

    @n_seismic_frames.setter
    def n_seismic_frames(self, value):
        self._n_seismic_frames = value

    @property
    def n_gravity_frames(self):
        return self._n_gravity_frames

    @n_gravity_frames.setter
    def n_gravity_frames(self, value):
        self._n_gravity_frames = value


class WallBuilding(Building):
    n_walls = 1
    wall_depth = 0.0  # m
    wall_width = 0.0  # m

    @property
    def inputs(self):
        input_list = super(WallBuilding, self).inputs
        new_inputs = [
            "n_walls",
            "wall_depth",
            "wall_width"
        ]
        return input_list + new_inputs


class Structure(PhysicalObject):
    """
    An object to describe structures.
    """
    _h_eff = None
    _mass_eff = None
    _t_fixed = None
    _mass_ratio = None

    inputs = [
        "h_eff",
        "mass_eff",
        "t_eff",
        "mass_ratio"
    ]

    @property
    def h_eff(self):
        return self._h_eff

    @h_eff.setter
    def h_eff(self, value):
        self._h_eff = value

    @property
    def mass_eff(self):
        return self._mass_eff

    @mass_eff.setter
    def mass_eff(self, value):
        self._mass_eff = value

    @property
    def t_fixed(self):
        return self._t_fixed

    @t_fixed.setter
    def t_fixed(self, value):
        self._t_fixed = value

    @property
    def mass_ratio(self):
        return self._mass_ratio

    @mass_ratio.setter
    def mass_ratio(self, value):
        self._mass_ratio = value

    @property
    def k_eff(self):
        return 4.0 * math.pi ** 2 * self.mass_eff / self.t_fixed ** 2

    @property
    def weight(self):
        return self.mass_eff / self.mass_ratio * 9.8


class SoilStructureSystem(PhysicalObject):
    bd = Structure()
    fd = Foundation()
    sp = Soil()
    hz = Hazard()
    name = "Nameless"

    inputs = ["name"] + bd.inputs + fd.inputs + sp.inputs + hz.inputs