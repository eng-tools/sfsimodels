import numbers
from collections import OrderedDict

import numpy as np

from sfsimodels.exceptions import ModelError, AnalysisError
from sfsimodels.models.abstract_models import PhysicalObject
from sfsimodels import checking_tools as ct


def clean_float(value):
    if value is None or value == "":
        return None
    return float(value)


class Soil(PhysicalObject):
    _id = None
    name = None
    stype = "soil"
    # strength parameters
    _phi = None
    _cohesion = None
    # volume and weight
    _e_min = None
    _e_max = None
    _e_curr = None
    _dilation_angle = None
    _relative_density = None  # [decimal]
    _specific_gravity = None
    _unit_dry_weight = None
    _unit_sat_weight = None
    _unit_moist_weight = None
    _saturation = None
    _pw = 9800  # N/m3  # specific weight of water
    _tolerance = 0.0001  # consistency tolerance
    _permeability = None
    # deformation parameters
    _g_mod = None  # Shear modulus [Pa]
    _bulk_mod = None  # Bulk modulus [Pa]
    _poissons_ratio = None

    inputs = [
        "id",
        "name",
        "stype",
        "g_mod",
        "bulk_mod",
        "poissons_ratio",
        "phi",
        "dilation_angle",
        "e_min",
        "e_max",
        "e_curr",
        "relative_density",
        "specific_gravity",
        "unit_dry_weight",
        "unit_sat_weight",
        "saturation",
        "cohesion",
        "permeability"
    ]

    def __init__(self):
        self.stack = []

    def to_dict(self):
        """
        Passes all of the inputs and the values to an ordered dictionary
        :return:
        """
        outputs = OrderedDict()
        for item in self.inputs:
            outputs[item] = self.__getattribute__(item)
        return outputs

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
            except ModelError:
                conflicts.append(item)
        return conflicts

    def reset_all(self):
        """
        Resets all parameters to None
        :return:
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

    @property
    def id(self):
        """
        Object id
        :return:
        """
        return self._id

    @property
    def unit_weight(self):
        """
        The unit moist weight of the soil (accounts for saturation level)
        :return:
        """
        if self.saturation is not None:
            return self.unit_moist_weight
        return self.unit_dry_weight

    @property
    def phi(self):
        """Internal friction angle of the soil"""
        return self._phi

    @property
    def dilation_angle(self):
        """
        Internal dilation angle of the soil

        peak_angle = phi + dilation_angle
        """
        return self._dilation_angle

    @property
    def cohesion(self):
        """Cohesive strength of the soil"""
        return self._cohesion

    @property
    def unit_dry_weight(self):
        """The unit weight of the soil if saturation=0"""
        return self._unit_dry_weight

    @property
    def e_curr(self):
        """The current void ratio of the soil"""
        return self._e_curr

    @property
    def specific_gravity(self):
        """The specific gravity of the soil"""
        return self._specific_gravity

    @property
    def saturation(self):
        """The current saturation of the soil"""
        return self._saturation

    @property
    def moisture_content(self):
        """
        The moisture of the soil :math:`(unit_moisture_weight) / (unit_dry_weight)`.
        """
        try:
            return self._unit_moisture_weight / self.unit_dry_weight
        except TypeError:
            return None

    @property
    def porosity(self):
        """Soil porosity"""
        try:
            return self.e_curr / (1 + self.e_curr)
        except TypeError:
            return None

    @property
    def unit_sat_weight(self):
        """The weight of the soil if saturation=1"""
        return self._unit_sat_weight

    @property
    def unit_moist_weight(self):
        """The unit moist weight of the soil (accounts for saturation level)"""
        return self._unit_moist_weight

    @property
    def permeability(self):
        """The permeability of the soil"""
        return self._permeability

    @property
    def phi_r(self):
        """internal friction angle in radians"""
        return np.radians(self.phi)

    @property
    def k_0(self):
        k_0 = 1 - np.sin(self.phi_r)  # Jaky 1944
        return k_0

    @property
    def g_mod(self):
        """Shear modulus of the soil"""
        return self._g_mod

    @property
    def bulk_mod(self):
        """Bulk modulus of the soil"""
        return self._bulk_mod

    @property
    def poissons_ratio(self):
        """Poisson's ratio of the soil"""
        return self._poissons_ratio

    @property
    def e_min(self):
        """The minimum void ratio"""
        return self._e_min

    @property
    def e_max(self):
        """The maximum void ratio"""
        return self._e_max

    @property
    def relative_density(self):
        """The relative density :math (e_max - e_curr) / (.e_max - .e_min)"""
        return self._relative_density

    @id.setter
    def id(self, value):
        self.stack.append(("id", value))
        self._id = value

    @e_curr.setter
    def e_curr(self, value):
        value = clean_float(value)
        if value is None:
            return
        try:
            void_ratio = self._calc_void_ratio()
            if void_ratio is not None and not ct.isclose(void_ratio, value, rel_tol=self._tolerance):
                raise ModelError("New void ratio (%.3f) inconsistent with one from specific_gravity (%.3f)"
                                 % (value, void_ratio))
        except TypeError:
            pass
        old_value = self._e_curr
        self._e_curr = float(value)
        try:
            self.recompute_all_weights_and_void()
            self._add_to_stack("e_curr", float(value))
        except ModelError as e:
            self._e_curr = old_value
            raise ModelError(e)

    @unit_dry_weight.setter
    def unit_dry_weight(self, value):
        value = clean_float(value)
        if value is None:
            return
        try:
            unit_dry_weight = self._calc_unit_dry_weight()
            if unit_dry_weight is not None and not ct.isclose(unit_dry_weight, value, rel_tol=self._tolerance):
                raise ModelError("new unit_dry_weight (%.2f) is inconsistent with calculated value (%.2f)." % (value, unit_dry_weight))
        except TypeError:
            pass
        old_value = self.unit_dry_weight
        self._unit_dry_weight = value
        try:
            self.recompute_all_weights_and_void()
            self._add_to_stack("unit_dry_weight", value)
        except ModelError as e:
            self._unit_dry_weight = old_value
            raise ModelError(e)

    @unit_sat_weight.setter
    def unit_sat_weight(self, value):
        value = clean_float(value)
        if value is None:
            return
        try:
            unit_sat_weight = self._calc_unit_sat_weight()
            if unit_sat_weight is not None and not ct.isclose(unit_sat_weight, value, rel_tol=self._tolerance):
                raise ModelError("new unit_sat_weight (%.2f) with calculated value (%.2f)." % (value, unit_sat_weight))
        except TypeError:
            pass
        old_value = self.unit_sat_weight
        self._unit_sat_weight = value
        try:
            self.recompute_all_weights_and_void()
            self._add_to_stack("unit_sat_weight", value)
        except ModelError as e:
            self._unit_sat_weight = old_value
            raise ModelError(e)

    @unit_moist_weight.setter
    def unit_moist_weight(self, value):
        value = clean_float(value)
        if value is None:
            return
        try:
            unit_moist_weight = self._calc_unit_moist_weight()
            if unit_moist_weight is not None and not ct.isclose(unit_moist_weight, value, rel_tol=self._tolerance):
                raise ModelError("new unit_moist_weight (%.2f) is inconsistent with calculated value (%.2f)." % (value, unit_moist_weight))
        except TypeError:
            pass
        old_value = self.unit_moist_weight
        self._unit_moist_weight = value
        try:
            self.recompute_all_weights_and_void()
            self._add_to_stack("unit_moist_weight", value)
        except ModelError as e:
            self._unit_moist_weight = old_value
            raise ModelError(e)

    @saturation.setter
    def saturation(self, value):
        """Volume of water to volume of voids"""
        value = clean_float(value)
        if value is None:
            return
        try:
            unit_moisture_weight = self.unit_moist_weight - self.unit_dry_weight
            unit_moisture_volume = unit_moisture_weight / self._pw
            saturation = unit_moisture_volume / self._unit_void_volume
            if saturation is not None and not ct.isclose(saturation, value, rel_tol=self._tolerance):
                raise ModelError("New saturation (%.3f) is inconsistent "
                                 "with calculated value (%.3f)" % (value, saturation))
        except TypeError:
            pass
        old_value = self.saturation
        self._saturation = value
        try:
            self.recompute_all_weights_and_void()
            self._add_to_stack("saturation", value)
        except ModelError as e:
            self._saturation = old_value
            raise ModelError(e)

    @relative_density.setter
    def relative_density(self, value):
        value = clean_float(value)
        if value is None:
            return

        relative_density = self._calc_relative_density()
        if relative_density is not None and not ct.isclose(relative_density, value, rel_tol=self._tolerance):
                raise ModelError("New relative_density (%.3f) is inconsistent "
                                 "with calculated value (%.3f)" % (value, relative_density))

        old_value = self.relative_density
        self._relative_density = value
        try:
            self.recompute_all_weights_and_void()
            self._add_to_stack("relative_density", value)
        except ModelError as e:
            self._relative_density = old_value
            raise ModelError(e)

    @specific_gravity.setter
    def specific_gravity(self, value):
        """ Set the relative weight of the solid """
        value = clean_float(value)
        if value is None:
            return
        specific_gravity = self._calc_specific_gravity()
        if specific_gravity is not None and not ct.isclose(specific_gravity, value, rel_tol=self._tolerance):
            raise ModelError("specific gravity is inconsistent with set unit_dry_weight and void_ratio")

        self._specific_gravity = float(value)
        self.stack.append(("specific_gravity", float(value)))
        self.recompute_all_weights_and_void()

    @e_min.setter
    def e_min(self, value):
        value = clean_float(value)
        if value is None:
            return
        self._e_min = value
        self.stack.append(("e_min", value))
        self.recompute_all_weights_and_void()

    @e_max.setter
    def e_max(self, value):
        value = clean_float(value)
        if value is None:
            return
        self._e_max = float(value)
        self.stack.append(("e_max", value))
        self.recompute_all_weights_and_void()

    @phi.setter
    def phi(self, value):
        value = clean_float(value)
        if value is None:
            return
        self._phi = value
        self.stack.append(("phi", value))

    @cohesion.setter
    def cohesion(self, value):
        value = clean_float(value)
        if value is None:
            return
        self._cohesion = value
        self.stack.append(("cohesion", value))

    @porosity.setter
    def porosity(self, value):
        value = clean_float(value)
        if value is None:
            return
        self._e_curr = value / (1 - value)
        self.stack.append(("e_curr", value))  # note that it is the set store variable that goes in the stack

    @dilation_angle.setter
    def dilation_angle(self, value):
        value = clean_float(value)
        if value is None:
            return
        self._dilation_angle = value
        self.stack.append(("dilation_angle", value))

    @permeability.setter
    def permeability(self, value):
        value = clean_float(value)
        if value is None:
            return
        self._permeability = value
        self.stack.append(("permeability", value))

    @g_mod.setter
    def g_mod(self, value):
        value = clean_float(value)
        if value is None:
            return
        curr_g_mod = self._calc_g_mod()
        if curr_g_mod is not None and not ct.isclose(curr_g_mod, value, rel_tol=0.001):
                raise ModelError("New g_mod is inconsistent with current value")
        old_value = self.g_mod
        self._g_mod = value
        try:
            self.recompute_all_stiffness_parameters()
            self._add_to_stack("g_mod", value)
        except ModelError as e:
            self._g_mod = old_value
            raise ModelError(e)

    @bulk_mod.setter
    def bulk_mod(self, value):
        value = clean_float(value)
        if value is None:
            return
        curr_bulk_mod = self._calc_bulk_mod()
        if curr_bulk_mod is not None and not ct.isclose(curr_bulk_mod, value, rel_tol=0.001):
                raise ModelError("New bulk_mod is inconsistent with current value")
        old_value = self.bulk_mod
        self._bulk_mod = value
        try:
            self.recompute_all_stiffness_parameters()
            self._add_to_stack("bulk_mod", value)
        except ModelError as e:
            self._bulk_mod = old_value
            raise ModelError(e)

    @poissons_ratio.setter
    def poissons_ratio(self, value):
        if value is None or value == "":
            return
        curr_poissons_ratio = self._calc_poissons_ratio()
        if curr_poissons_ratio is not None and not ct.isclose(curr_poissons_ratio, value, rel_tol=0.001):
                raise ModelError("New poissons_ratio (%.3f) is inconsistent "
                                 "with current value (%.3f)" % (value, curr_poissons_ratio))
        old_value = self.poissons_ratio
        self._poissons_ratio = value
        try:
            self.recompute_all_stiffness_parameters()
            self._add_to_stack("poissons_ratio", value)
        except ModelError as e:
            self._poissons_ratio = old_value
            raise ModelError(e)

    def _calc_unit_sat_weight(self):
        try:
            return self._unit_void_volume * self._pw + self.unit_dry_weight
        except TypeError:
            return None

    def _calc_unit_moist_weight(self):
        try:
            return self._unit_moisture_weight + self.unit_dry_weight
        except TypeError:
            return None

    def _calc_saturation(self):
        try:
            unit_moisture_weight = self.unit_moist_weight - self.unit_dry_weight
            unit_moisture_volume = unit_moisture_weight / self._pw
            return unit_moisture_volume / self._unit_void_volume
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

    def _calc_g_mod(self):
        try:
            return 3 * self.bulk_mod * (1 - 2 * self.poissons_ratio) / (2 * (1 + self.poissons_ratio))
        except TypeError:
            return None

    def _calc_bulk_mod(self):
        try:
            return 2 * self.g_mod * (1 + self.poissons_ratio) / (3 * (1 - 2 * self.poissons_ratio))
        except TypeError:
            return None

    def _calc_poissons_ratio(self):
        try:
            return (3 * self.bulk_mod - 2 * self.g_mod) / (2 * (3 * self.bulk_mod + self.g_mod))
        except TypeError:
            return None

    def recompute_all_weights_and_void(self):
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
        f_map["_unit_moist_weight"] = self._calc_unit_moist_weight
        f_map["_saturation"] = self._calc_saturation

        for item in f_map:
            value = f_map[item]()
            if value is not None:
                curr_value = getattr(self, item)
                if curr_value is not None and not ct.isclose(curr_value, value, rel_tol=0.001):
                    raise ModelError("new %s is inconsistent with current value (%.3f, %.3f)" % (item, curr_value,
                                                                                                           value))
                setattr(self, item, value)

    def recompute_all_stiffness_parameters(self):
        f_map = OrderedDict()
        # voids
        f_map["_g_mod"] = self._calc_g_mod
        f_map["_bulk_mod"] = self._calc_bulk_mod

        f_map["_poissons_ratio"] = self._calc_poissons_ratio

        for item in f_map:
            value = f_map[item]()
            if value is not None:
                curr_value = getattr(self, item)
                if curr_value is not None and not ct.isclose(curr_value, value, rel_tol=0.001):
                    raise ModelError("new %s is inconsistent with current value (%.3f, %.3f)" % (item, curr_value,
                                                                                                           value))
                setattr(self, item, value)

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


class CriticalSoil(Soil):
    # critical state parameters
    e_cr0 = 0.0
    p_cr0 = 0.0
    lamb_crl = 0.0

    def __init__(self):
        super(CriticalSoil, self).__init__()  # run parent class initialiser function

    @property
    def inputs(self):
        input_list = super(CriticalSoil, self).inputs
        new_inputs = [
        "e_cr0",
        "p_cr0",
        "lamb_crl"
        ]
        return input_list + new_inputs

    def e_critical(self, p):
        p = float(p)
        return self.e_cr0 - self.lamb_crl * np.log(p / self.p_cr0)


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
    _gwl = 1e6  # Ground water level [m]
    unit_weight_water = 9800.  # [N/m3]  # DEPRECATED
    unit_water_weight = 9800.  # [N/m3]
    _height = None

    inputs = [
        "id",
        "name",
        "gwl",
        "unit_water_weight",
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
        self._id = int(value)

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

    def layer_height(self, layer_int):
        """
        The number of the layer.
        :param layer_int:
        :return:
        """
        if layer_int == len(self.layers):
            if self.height is None:
                return None
            return self.height - self.layer_depth(layer_int)
        else:
            return self.layer_depth(layer_int + 1) - self.layer_depth(layer_int)

    @property
    def layers(self):
        return self._layers

    def remove_layer(self, depth):
        del self._layers[depth]

    def layer(self, index):
        index = int(index)
        if index == 0:
            raise KeyError("index=%i, but must be 1 or greater." % index)
        return list(self._layers.values())[index - 1]

    def layer_depth(self, index):
        index = int(index)
        if index == 0:
            raise KeyError("index=%i, but must be 1 or greater." % index)
        return self.depths[index - 1]

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
            crust_phi_r = np.radians(crust.phi)
            equivalent_cohesion = crust.cohesion + crust.k_0 * self.crust_effective_unit_weight * \
                                                    self.layer_depth(1) / 2 * np.tan(crust_phi_r)
            return equivalent_cohesion

    @property
    def crust_effective_unit_weight(self):
        if len(self.layers) > 1:
            crust = self.layer(0)
            crust_height = self.layer_depth(1)
            total_stress_base = crust_height * crust.unit_weight
            pore_pressure_base = (crust_height - self.gwl) * self.unit_water_weight
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
        end = 0
        for layer_int in range(1, len(depths) + 1):
            l_index = layer_int - 1
            if z_c > depths[layer_int - 1]:
                if l_index < len(depths) - 1 and z_c > depths[l_index + 1]:
                    height = depths[l_index + 1] - depths[l_index]
                    bottom_depth = depths[l_index + 1]
                else:
                    end = 1
                    height = z_c - depths[l_index]
                    bottom_depth = z_c

                if bottom_depth <= self.gwl:
                    total_stress += height * self.layer(layer_int).unit_dry_weight
                else:
                    if self.layer(layer_int).unit_sat_weight is None:
                        raise AnalysisError("Saturated unit weight not defined for layer %i." % layer_int)
                    sat_height = bottom_depth - max(self.gwl, depths[l_index])
                    dry_height = height - sat_height
                    total_stress += dry_height * self.layer(layer_int).unit_dry_weight + \
                                    sat_height * self.layer(layer_int).unit_sat_weight
            else:
                end = 1
            if end:
                break
        return total_stress

    def hydrostatic_pressure(self, y_c):
        """
        Determine the vertical effective stress at a single depth y_c.
        """
        return max(y_c - self.gwl, 0.0) * self.unit_water_weight

    def vertical_effective_stress(self, y_c):
        """
        Determine the vertical effective stress at a single depth z_c.
        """
        sigma_v_c = self.vertical_total_stress(y_c)
        pp = self.hydrostatic_pressure(y_c)
        sigma_veff_c = sigma_v_c - pp
        return sigma_veff_c

# TODO: extend to have LiquefiableSoil