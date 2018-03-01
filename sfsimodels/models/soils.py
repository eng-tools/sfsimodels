import numbers
from collections import OrderedDict

import numpy as np

import math
from sfsimodels.exceptions import ModelError
from sfsimodels.models.abstract_models import PhysicalObject
from sfsimodels import checking_tools as ct


class Soil(PhysicalObject):
    id = None
    name = None
    # strength parameters
    _phi = None
    _cohesion = None
    # volume and weight
    _unit_dry_weight = None
    _e_min = None
    _e_max = None
    _e_curr = None
    _dilation_angle = None
    _relative_density = None  # [decimal]
    _specific_gravity = None
    _unit_sat_weight = None
    _saturation = None
    _pw = 9800  # N/m3  # specific weight of water
    _permeability = None
    # deformation parameters
    _g_mod = None  # Shear modulus [Pa]
    _bulk_mod = None  # Bulk modulus [Pa]
    _poissons_ratio = None
    # critical state parameters
    e_cr0 = 0.0
    p_cr0 = 0.0
    lamb_crl = 0.0

    inputs = [
        "id",
        "name",
        "g_mod",
        "bulk_mod",
        "phi",
        "dilation_angle",
        "relative_density",
        "unit_dry_weight",
        "unit_sat_weight",
        "cohesion",
        "poissons_ratio",
        "e_min",
        "e_max",
        "e_curr",
        "e_cr0",
        "p_cr0",
        "lamb_crl"
    ]

    def to_dict(self):
        outputs = OrderedDict()
        for item in self.inputs:
            outputs[item] = self.__getattribute__(item)
        return outputs

    @property
    def unit_weight(self):
        if self.saturation is not None:
            return self._unit_moisture_weight + self.unit_dry_weight
        return self.unit_dry_weight

    @property
    def phi(self):
        return self._phi

    @property
    def dilation_angle(self):
        return self._dilation_angle

    @property
    def cohesion(self):
        return self._cohesion

    @property
    def unit_dry_weight(self):
        return self._unit_dry_weight

    @property
    def e_curr(self):
        return self._e_curr

    @property
    def specific_gravity(self):
        return self._specific_gravity

    @property
    def saturation(self):
        return self._saturation

    @property
    def moisture_content(self):
        try:
            return self._unit_moisture_weight / self.unit_dry_weight
        except TypeError:
            return None

    @property
    def porosity(self):
        try:
            return self.e_curr / (1 + self.e_curr)
        except TypeError:
            return None

    @property
    def unit_sat_weight(self):
        return self._unit_sat_weight

    @property
    def permeability(self):
        return self._permeability

    @property
    def phi_r(self):
        return math.radians(self.phi)

    @property
    def k_0(self):
        k_0 = 1 - math.sin(self.phi_r)  # Jaky 1944
        return k_0

    @property
    def g_mod(self):
        return self._g_mod

    @property
    def bulk_mod(self):
        return self._bulk_mod

    @property
    def poissons_ratio(self):
        return self._poissons_ratio

    @property
    def e_min(self):
        return self._e_min

    @property
    def e_max(self):
        return self._e_max

    @property
    def relative_density(self):
        return self._relative_density

    @e_curr.setter
    def e_curr(self, value, override=False):
        try:
            void_ratio = self._calc_void_ratio()
            if void_ratio is not None and not ct.isclose(void_ratio, value) and not override:
                raise ModelError("New void ratio (%.3f) inconsistent with one from specific_gravity (%.3f)"
                                 % (value, void_ratio))
        except TypeError:
            pass
        self._e_curr = value
        self.recompute_all()
        # unit_dry_weight = self._calc_unit_dry_weight()
        # if unit_dry_weight is not None and unit_dry_weight != self.unit_dry_weight:
        #     self.unit_dry_weight = unit_dry_weight
        # specific_gravity = self._calc_specific_gravity()
        # if specific_gravity is not None and specific_gravity != self.specific_gravity:
        #     self.specific_gravity = specific_gravity

    @unit_dry_weight.setter
    def unit_dry_weight(self, value, override=False):
        self._unit_dry_weight = value
        if self.e_curr is not None:
            specific_gravity = self._calc_specific_gravity()
            if self.specific_gravity is not None and not override:
                if self._specific_gravity != specific_gravity:
                    raise ModelError("New unit dry weight is inconsistent with specific gravity and void ratio")
            else:
                self._specific_gravity = specific_gravity
        self.e_curr = self._calc_void_ratio()

    @unit_sat_weight.setter
    def unit_sat_weight(self, value):
        try:
            unit_sat_weight = self._calc_unit_sat_weight()
            if unit_sat_weight is not None and unit_sat_weight != value:
                raise ModelError("new unit_sat_weight is inconsistent with other soil parameters")
        except TypeError:
            pass
        self._unit_sat_weight = value
        # try to set other parameters
        if self.unit_dry_weight is not None:
            unit_moisture_weight = self.unit_sat_weight - self.unit_dry_weight
            unit_moisture_volume = unit_moisture_weight / self._pw
            if self.e_curr is not None:  # can set saturation
                self.saturation = unit_moisture_volume / self._unit_void_volume
            if self.saturation is not None:
                unit_void_volume = unit_moisture_volume / self.saturation
                if self.specific_gravity is not None:
                    # set the dry weight and automatically sets the current void ratio
                    self.unit_dry_weight = (1 - unit_void_volume) * self.specific_gravity * self._pw
                elif self.e_curr is not None:
                    self.unit_dry_weight = self.unit_sat_weight - unit_moisture_weight

    @saturation.setter
    def saturation(self, value, override=False):
        """Volume of water to volume of voids"""
        try:
            unit_moisture_weight = self.unit_sat_weight - self.unit_dry_weight
            unit_moisture_volume = unit_moisture_weight / self._pw
            saturation = unit_moisture_volume / self._unit_void_volume
            if saturation is not None and saturation != value and override:
                raise ModelError("new saturation is inconsistent with unit weights")
        except TypeError:
            pass
        self._saturation = value
        unit_sat_weight = self._calc_unit_sat_weight()
        if unit_sat_weight is not None and unit_sat_weight != self.unit_sat_weight:
            self.unit_sat_weight = unit_sat_weight
        # TODO: calculate dry weight from values

    @relative_density.setter
    def relative_density(self, value, override=False):
        try:
            relative_density = self._calc_relative_density()
            if relative_density is not None and not ct.isclose(relative_density, value, rel_tol=0.001) and not override:
                    raise ModelError("New relative_density is inconsistent with e_curr")

        except TypeError:
            pass
        self._relative_density = value
        self.recompute_all()


    @specific_gravity.setter
    def specific_gravity(self, value, override=False):
        """ Set the relative weight of the solid """
        specific_gravity = self._calc_specific_gravity()
        if specific_gravity is not None and specific_gravity != value and override is False:
            raise ModelError("specific gravity is inconsistent with set unit_dry_weight and void_ratio")

        self._specific_gravity = value
        self.recompute_all()

    def recompute_all(self):
        # TODO: catch potential inconsistency when void ratio get defined based on weight and the again from saturation
        f_map = OrderedDict()
        # voids
        f_map["_e_curr"] = self._calc_void_ratio
        f_map["_relative_density"] = self._calc_relative_density

        f_map["_e_min"] = self._calc_min_void_ratio
        f_map["_e_max"] = self._calc_max_void_ratio
        # weights
        f_map["_unit_dry_weight"] = self._calc_unit_dry_weight
        f_map["_specific_gravity"] = self._calc_specific_gravity
        # saturation
        f_map["_unit_sat_weight"] = self._calc_unit_sat_weight

        for item in f_map:
            value = f_map[item]()
            if value is not None:
                curr_value = getattr(self, item)
                if curr_value is not None and not ct.isclose(curr_value, value, rel_tol=0.001):
                    raise ModelError("new value is inconsistent with current %s parameter (%.3f, %.3f)" % (item,
                                                                                                           curr_value,
                                                                                                           value))
                setattr(self, item, value)

    @e_min.setter
    def e_min(self, value):
        self._e_min = value
        self.recompute_all()

    @e_max.setter
    def e_max(self, value):
        self._e_max = value
        self.recompute_all()

    @phi.setter
    def phi(self, value):
        self._phi = value

    @cohesion.setter
    def cohesion(self, value):
        self._cohesion = value

    @porosity.setter
    def porosity(self, value):
        self._e_curr = value / (1 - value)

    @dilation_angle.setter
    def dilation_angle(self, value):
        self._dilation_angle = value

    @permeability.setter
    def permeability(self, value):
        self._permeability = value

    @g_mod.setter
    def g_mod(self, value):
        self._g_mod = value

    @bulk_mod.setter
    def bulk_mod(self, value):
        self._bulk_mod = value

    @poissons_ratio.setter
    def poissons_ratio(self, value):  # TODO: add correlation between g_mod and bulk_mod
        self._poissons_ratio = value

    def e_critical(self, p):
        p = float(p)
        return self.e_cr0 - self.lamb_crl * math.log(p / self.p_cr0)

    def n1_60(self):  # TODO: move to be a function
        return (self.relative_density * 100. / 15) ** 2

    def _calc_unit_sat_weight(self):
        try:
            return self._unit_moisture_weight + self.unit_dry_weight
        except TypeError:
            return None

    def _calc_relative_density(self):
        try:
            return (self.e_max - self.e_curr) / (self.e_max - self.e_min)
        except TypeError:
            return None

    def _calc_specific_gravity(self):
        try:
            return (1 + self.e_curr) * self.unit_dry_weight / self._pw
        except TypeError:
            return None

    def _calc_unit_dry_weight(self):
        try:
            return (self.specific_gravity * self._pw) / (1 + self.e_curr)  # dry relationship
        except TypeError:
            return None

    def _calc_void_ratio(self):
        try:
            return self.specific_gravity * self._pw / self.unit_dry_weight - 1
        except TypeError:
            pass
        try:
            return self.e_max - self.relative_density * (self.e_max - self.e_min)
        except TypeError:
            return None

    def _calc_max_void_ratio(self):
        try:
            # return (self.e_curr - self.relative_density) / (1. - self.relative_density)
            return (self.relative_density * self.e_min - self.e_curr) / (self.relative_density - 1)
        except TypeError:
            return None

    def _calc_min_void_ratio(self):
        try:
            return (self.e_curr + (self.relative_density - 1) * self.e_max) / self.relative_density
        except TypeError:
            return None

    @property
    def _unit_void_volume(self):
        """Return the volume of the voids for total volume equal to a unit"""
        return self.e_curr / (1 + self.e_curr)

    @property
    def _unit_solid_volume(self):
        """Return the volume of the solids for total volume equal to a unit"""
        return 1.0 - self._unit_solid_volume

    @property
    def _unit_moisture_weight(self):
        """Return the weight of the voids for total volume equal to a unit"""
        return self.saturation * self._unit_void_volume * self._pw


class SoilLayer(Soil):

    def __init__(self, depth=0.0, height=1000, top_total_stress=0.0, top_pore_pressure=0.0):
        self.height = height  # m  from top of layer to bottom of layer
        self.depth = depth  # m from ground surface to top of layer
        self.top_total_stress = top_total_stress  # m total vertical stress at the top
        self.top_pore_pressure = top_pore_pressure  # m pore pressure at the top


class SoilProfile(PhysicalObject):
    """
    An object to describe a soil profile
    """
    _id = None
    name = None
    _gwl = None  # Ground water level [m]
    unit_weight_water = 9800.  # [N/m3]
    _height = None

    inputs = [
        "id",
        "name",
        "gwl",
        "unit_weight_water",
        "layers",
        "height"
    ]

    def __init__(self):
        super(PhysicalObject, self).__init__()  # run parent class initialiser function
        self._layers = OrderedDict([(0, Soil())])  # [depth to top of layer, Soil object]

    def __str__(self):
        return "SoilProfile id: {0}, name: {1}".format(self.id, self.name)

    def to_dict(self):
        outputs = OrderedDict()
        skip_list = ["layers"]
        for item in self.inputs:
            if item not in skip_list:
                value = self.__getattribute__(item)
                if isinstance(value, int):
                    outputs[item] = str(value)
                else:
                    outputs[item] = value
        # outputs["layers"] = []
        # for depth in self.layers:
        #     outputs["layers"].append({"depth": float(depth), "soil": self.layers[depth].to_dict()})
        return outputs

    def add_layer(self, depth, soil):
        self._layers[depth] = soil
        self._sort_layers()

    def _sort_layers(self):
        """
        Sort the layers by depth.
        :return:
        """
        self._layers = OrderedDict(sorted(self._layers.items(), key=lambda t: t[0]))

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    @property
    def gwl(self):
        return self._gwl

    @gwl.setter
    def gwl(self, value):
        self._gwl = float(value)

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        self._height = float(value)

    @property
    def layers(self):
        return self._layers

    def remove_layer(self, depth):
        del self._layers[depth]

    def layer(self, index):
        return list(self._layers.values())[index]

    def layer_depth(self, index):
        return self.depths[index]

    @property
    def n_layers(self):
        """
        Number of soil layers
        :return:
        """
        return len(self._layers)

    @property
    def depths(self):
        """
        An ordered list of depths.
        :return:
        """
        return list(self._layers.keys())

    @property
    def equivalent_crust_cohesion(self):
        """
        Calculate the equivalent crust cohesion strength according to Karamitros et al. 2013 sett, pg 8 eq. 14
        :return: equivalent cohesion [Pa]
        """
        if len(self.layers) > 1:
            crust = self.layer(0)
            crust_phi_r = math.radians(crust.phi)
            equivalent_cohesion = crust.cohesion + crust.k_0 * self.crust_effective_unit_weight * \
                                                    self.layer_depth(1) / 2 * math.tan(crust_phi_r)
            return equivalent_cohesion

    @property
    def crust_effective_unit_weight(self):
        if len(self.layers) > 1:
            crust = self.layer(0)
            crust_height = self.layer_depth(1)
            total_stress_base = crust_height * crust.unit_weight
            pore_pressure_base = (crust_height - self.gwl) * self.unit_weight_water
            unit_weight_eff = (total_stress_base - pore_pressure_base) / crust_height
            return unit_weight_eff

    def vertical_total_stress(self, z):
        """
        Determine the vertical total stress at depth z, where z can be a number or an array of numbers.
        """

        if isinstance(z, numbers.Real):
            return self.one_vertical_total_stress(z)
        else:
            sigma_v_effs = []
            for value in z:
                sigma_v_effs.append(self.one_vertical_total_stress(value))
            return np.array(sigma_v_effs)

    def one_vertical_total_stress(self, z_c):
        """
        Determine the vertical total stress at a single depth z_c.
        """
        total_stress = 0.0
        depths = self.depths
        for i in range(len(depths)):
            if z_c > depths[i]:
                if i < len(depths) - 1 and z_c > depths[i + 1]:
                    height = depths[i + 1] - depths[i]
                    total_stress += height * self.layer(i).unit_weight
                else:
                    height = z_c - depths[i]
                    total_stress += height * self.layer(i).unit_weight
                    break
        return total_stress

    def vertical_effective_stress(self, z_c):
        """
        Determine the vertical effective stress at a single depth z_c.
        """
        sigma_v_c = self.vertical_total_stress(z_c)
        sigma_veff_c = sigma_v_c - max(z_c - self.gwl, 0.0) * self.unit_weight_water
        return sigma_veff_c

# TODO: extend to have LiquefiableSoil