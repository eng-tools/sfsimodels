import math
import numbers
import numpy as np

from collections import OrderedDict

from sfsimodels.loader import add_inputs_to_object

__author__ = 'maximmillen'


class Soil(OrderedDict):
    """
    An object to describe a soil profile
    """
    g_mod = 0.0  # Shear modulus [Pa]
    phi = 0.0  # Critical friction angle [degrees]
    relative_density = 0.0  # [decimal]
    height_crust = None  # [m]
    height_liq = None  # Height of liquefiable layer [m]
    gwl = None  # Ground water level [m]
    unit_weight_crust = None  # N/m3
    unit_sat_weight_liq = None  # TODO: use specific gravity and void ratio
    unit_weight_water = 9800.  # [N/m3]
    crust_cohesion = 0.0  # [Pa]
    crust_phi = 0.0  # [degrees]
    poissons_ratio = 0.0
    e_min = 0.0
    e_max = 0.0
    e_cr0 = 0.0
    p_cr0 = 0.0
    lamb_crl = 0.0
    clay_crust = True  # deprecated

    inputs = [
        "g_mod",
        "phi",
        "relative_density",
        "height_crust",
        "height_liq",
        "gwl",
        "unit_weight_crust",
        "unit_sat_weight_liq",
        "unit_weight_water",
        "crust_cohesion",
        "crust_phi",
        "poissons_ratio",
        "e_min",
        "e_max",
        "e_cr0",
        "p_cr0",
        "lamb_crl"
    ]

    # Calculated values
    phi_r = None
    e_initial = None
    k_0 = None

    @property
    def e_initial(self):
        return self.e_max - self.relative_density * (self.e_max - self.e_min)

    @property
    def phi_r(self):
        return math.radians(self.phi)

    @property
    def k_0(self):
        k_0 = 1 - math.sin(self.phi_r)  # Jaky 1944
        return k_0

    def e_cr(self, p):
        p = float(p)
        return self.e_cr0 - self.lamb_crl * math.log(p / self.p_cr0)

    @property
    def equivalent_crust_cohesion(self):
        """
        Calculate the equivalent crust cohesion strength according to Karamitros et al. 2013 sett, pg 8 eq. 14
        :return: equivalent cohesion [Pa]
        """
        crust_phi_r = math.radians(self.crust_phi)
        equivalent_cohesion = self.crust_cohesion + self.k_0 * self.crust_effective_unit_weight * \
                                                    self.height_crust / 2 * math.tan(crust_phi_r)
        return equivalent_cohesion

    @property
    def crust_effective_unit_weight(self):
        total_stress_base = self.height_crust * self.unit_weight_crust
        pore_pressure_base = (self.height_crust - self.gwl) * self.unit_weight_water
        unit_weight_eff = (total_stress_base - pore_pressure_base) / self.height_crust
        return unit_weight_eff

    @property
    def n1_60(self):
        return (self.relative_density * 100. / 15) ** 2

    def vertical_total_stress(self, z):
        if isinstance(z, numbers.Real):
            return self.one_vertical_total_stress(z)
        else:
            sigma_v_effs = []
            for value in z:
                sigma_v_effs.append(self.one_vertical_total_stress(value))
            return np.array(sigma_v_effs)

    def one_vertical_total_stress(self, z_c):
        if z_c <= self.height_crust:
            return z_c * self.unit_weight_crust
        else:
            return self.height_crust * self.unit_weight_crust + (z_c - self.height_crust) * self.unit_sat_weight_liq

    def vertical_effective_stress(self, z_c):
        sigma_v_c = self.vertical_total_stress(z_c)
        sigma_veff_c = sigma_v_c - (z_c - self.gwl) * self.unit_weight_water
        return sigma_veff_c


class Hazard(OrderedDict):
    """
    An object to describe seismic hazard.
    """
    z_factor = 0.0
    r_factor = 1.0
    n_factor = 1.0
    magnitude = 0.0
    corner_period = 0.0
    corner_acc_factor = 0.0

    inputs = [
        "z_factor",
        "r_factor",
        "n_factor",
        "magnitude",
        "corner_period",
        "corner_acc_factor"
    ]

    # Calculated values
    outputs = [
        "pga",
        "corner_acc",
        "corner_disp",
    ]

    @property
    def pga(self):
        return self.z_factor * self.r_factor * self.n_factor

    @property
    def corner_acc(self):
        return self.corner_acc_factor * self.z_factor * self.r_factor * self.n_factor * 9.8

    @property
    def corner_disp(self):
        return self.corner_acc / (2 * math.pi / self.corner_period) ** 2

    @property
    def msf(self):  # TODO: move this to functions.py
        """
        Magnitude scaling factor
        :return:
        """
        msf = 10. ** 2.24 / self.magnitude ** 2.56
        return msf


class Foundation(OrderedDict):
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
        return self.length ** 3 * self.width / 12

    @property
    def mass(self):
        return self.width * self.depth * self.height * self.density

    @property
    def weight(self):
        return self.mass * 9.8

    @property
    def inputs(self):
        input_list = super(RaftFoundation, self).inputs
        new_inputs = [
            "i_ww",
        ]
        return input_list + new_inputs


class Structure(OrderedDict):
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


class Concrete(OrderedDict):
    """
    An object to describe reinforced concrete
    """
    fy = 300.0e6  # Pa
    youngs_steel = 200e9  # Pa

    inputs = [
            'fy',
            'youngs_steel'
    ]


class Building(OrderedDict):
    """
    An object to define Buildings
    """
    floor_length = 10.0  # m
    floor_width = 10.0  # m
    concrete = Concrete()
    _interstorey_heights = np.array([3.4])  # m
    _storey_masses = np.array([40.0e3])  # kg
    g = 9.81  # m/s2  # gravity

    inputs = [
        'floor_length',
        'floor_width',
        'interstorey_heights',
        'n_storeys'
    ]

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
    _bay_lengths = np.array([6])  # protected
    _beam_depths = np.array([.5])  # protected
    n_seismic_frames = 2
    n_gravity_frames = 0

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

    def set(self, values):
        """""
        Set the frame object parameters using a dictionary
        """""
        add_inputs_to_object(self, values)


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

    @property
    def inputs(self):
        input_list = super(WallBuilding, self).inputs
        new_inputs = [
        "bay_lengths",
        "beam_depths",
        "n_seismic_frames",
        "n_gravity_frames"
    ]
        return input_list + new_inputs


class SoilStructureSystem(OrderedDict):
    bd = Structure()
    fd = Foundation()
    sp = Soil()
    hz = Hazard()
    name = "Nameless"

    inputs = [
        "name"
    ] + bd.inputs + fd.inputs + sp.inputs + hz.inputs
