import math
import numbers


import numpy as np

from sfsimodels.exceptions import ModelError
from sfsimodels.models.abstract_models import PhysicalObject
from sfsimodels.models import Hazard, Foundation, Soil


class Concrete(PhysicalObject):
    """
    An object to describe reinforced concrete
    """
    physical_type = "concrete"

    def __init__(self, fc=30.0e6, fy=300.0e6, youngs_steel=200e9, piossons_ratio=0.18):
        self.fc = fc  # Pa
        self.fy = fy  # Pa
        self.youngs_steel = youngs_steel  # Pa
        self.poissons_ratio = piossons_ratio

    inputs = [
            'fy',
            'youngs_steel'
    ]

    @property
    def youngs_concrete(self):
        return (3320 * np.sqrt(self.fc / 1e6) + 6900.0) * 1e6


class Building(PhysicalObject):
    """
    An object to define Buildings
    """
    physical_type = "building"
    g = 9.81  # m/s2  # gravity

    inputs = [
        'floor_length',
        'floor_width',
        'interstorey_heights',
        'n_storeys'
    ]

    def __init__(self, floor_length=10, floor_width=10, interstorey_height=3.4, storey_mass=40.e3):
        self.floor_length = floor_length  # m
        self.floor_width = floor_width  # m
        self.concrete = Concrete()
        self._interstorey_heights = np.array([interstorey_height])  # m
        self._storey_masses = np.array([storey_mass])  # kg

    @property
    def floor_area(self):
        return self.floor_length * self.floor_width

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

    def __init__(self, bay_length=6, beam_depth=0.5, n_seismic_frames=0, n_gravity_frames=0,
                 floor_length=10, floor_width=10, interstorey_height=3.4, storey_mass=40.e3):
        # run parent class initialiser function
        super(Building, self).__init__(floor_length=floor_length, floor_width=floor_width,
                                       interstorey_height=interstorey_height, storey_mass=storey_mass)
        self.n_seismic_frames = n_seismic_frames
        self.n_gravity_frames = n_gravity_frames
        self._bay_lengths = np.array([bay_length])
        self._beam_depths = np.array([beam_depth])

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
    h_eff = None
    mass_eff = None
    t_fixed = None
    mass_ratio = None

    inputs = [
        "h_eff",
        "mass_eff",
        "t_eff",
        "mass_ratio"
    ]

    # calculated values
    k_eff = None
    weight = None

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

    inputs = [
        "name"
    ] + bd.inputs + fd.inputs + sp.inputs + hz.inputs

