from collections import OrderedDict
from sfsimodels.exceptions import deprecation

import numpy as np

from sfsimodels.exceptions import ModelError, AnalysisError
from sfsimodels.functions import clean_float
from sfsimodels.models.abstract_models import PhysicalObject
from sfsimodels import checking_tools as ct
from sfsimodels import functions as sf


MASS_DENSITY_WATER = 1.0e3


class Soil(PhysicalObject):
    """
    An object to simulate an element of soil
    """
    _id = None
    name = None
    base_type = "soil"
    type = "soil"
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
    _tolerance = 0.0001  # consistency tolerance
    _permeability = None
    # deformation parameters
    _g_mod = None  # Shear modulus [Pa]
    _bulk_mod = None  # Bulk modulus [Pa]
    _poissons_ratio = None
    _plasticity_index = None

    def __init__(self, pw=9800, liq_mass_density=None, g=9.8, **kwargs):
        # Note: pw has deprecated
        self._gravity = g  # m/s2
        if liq_mass_density:
            self._liq_mass_density = liq_mass_density  # kg/m3
        elif pw is not None and self._gravity is not None:
            if pw == 9800 and g == 9.8:
                self._liq_mass_density = 1.0e3
            else:
                self._liq_mass_density = pw / self._gravity
        else:
            self._liq_mass_density = None
        self.stack = [('gravity', self._gravity), ('liq_mass_density', self._liq_mass_density)]
        self._extra_class_inputs = [
            "id",
            "name",
            "base_type",
            "type",
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
            "plasticity_index",
            "permeability",
            "gravity",
            "liq_mass_density"
        ]
        if not hasattr(self, "inputs"):
            self.inputs = []
        self.inputs += list(self._extra_class_inputs)
        for param in kwargs:
            if param in self.inputs:
                setattr(self, param, kwargs[param])

    @property
    def ancestor_types(self):
        """View list of types from inherited objects"""
        parent_ancestor_types = super(Soil, self).ancestor_types
        return parent_ancestor_types + ["soil"]

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
                if item in ['gravity', 'liq_mass_density']:
                    self._add_to_stack(item, value)
            except ModelError:
                conflicts.append(item)
        return conflicts

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

    @property
    def id(self):
        """Object id"""
        return self._id

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
    def pw(self):
        """Specific weight of water"""
        deprecation('Soil.pw is deprecated, will be removed. Use Soil.ulw')
        return self.ulw

    @property
    def liq_mass_density(self):
        return self._liq_mass_density

    @property
    def gravity(self):
        return self._gravity

    @property
    def g(self):
        return self._gravity

    @gravity.setter
    def gravity(self, value):
        self._gravity = value

    @g.setter
    def g(self, value):
        self._gravity = value

    @liq_mass_density.setter
    def liq_mass_density(self, value):
        value = clean_float(value)
        if self._liq_mass_density is not None and not np.isclose(self._liq_mass_density, value, rtol=self._tolerance):
            raise ModelError("New liq_mass_density (%.3f) inconsistent with one (%.3f)"
                             % (value, self._liq_mass_density))
        if value is not None:
            self._liq_mass_density = float(value)
        else:
            self._liq_mass_density = None

    @property
    def ulw(self):
        """Unit weight of liquid"""
        return self.g * self.liq_mass_density

    @property
    def saturation(self):
        """The current saturation of the soil"""
        return self._saturation

    @property
    def plasticity_index(self):
        """The plasticity index of the soil"""
        return self._plasticity_index

    @property
    def moisture_content(self):
        """
        The moisture of the soil :math:`(unit_moisture_weight) / (unit_dry_weight)`.
        """
        try:
            return self._calc_unit_moisture_weight() / self.unit_dry_weight
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
    def unit_moist_mass(self):
        """The unit moist mass of the soil (accounts for saturation level)"""
        return self._unit_moist_weight / self._gravity

    @property
    def unit_bouy_weight(self):
        """The unit moist weight of the soil (accounts for saturation level)"""
        try:
            return self._unit_sat_weight - self.ulw
        except TypeError:
            return None

    @property
    def unit_weight(self):
        """
        The unit moist weight of the soil (accounts for saturation level)
        :return: float
        """
        if self.saturation is not None:
            return self.unit_moist_weight
        return self.unit_dry_weight

    def get_unit_weight_or(self, alt='none'):
        if self.saturation is not None:
            return self.unit_moist_weight
        elif alt == 'dry':
            return self.unit_dry_weight
        elif alt == 'sat':
            return self.unit_sat_weight
        return None


    @property
    def unit_dry_mass(self):
        """The mass of the soil in dry state"""
        try:
            return self._unit_dry_weight / self._gravity
        except TypeError:
            return None

    @property
    def unit_sat_mass(self):
        """The mass of the soil when fully saturated"""
        try:
            return self._unit_sat_weight / self._gravity
        except TypeError:
            return None

    def get_shear_vel(self, saturated):
        """
        Calculate the shear wave velocity

        :param saturated: bool, if true then use saturated mass
        :return:
        """
        try:
            if saturated:
                return np.sqrt(self.g_mod / self.unit_sat_mass)
            else:
                return np.sqrt(self.g_mod / self.unit_dry_mass)
        except TypeError:
            return None

    def calc_shear_vel(self, saturated):
        deprecation("Use get_shear_vel")
        return self.get_shear_vel(saturated)

    def get_unit_mass(self, saturated):
        if saturated:
            return self.unit_sat_mass
        else:
            return self.unit_dry_mass

    @property
    def permeability(self):
        """The permeability of the soil"""
        return self._permeability

    @property
    def phi_r(self):
        """internal friction angle in radians"""
        try:
            return np.radians(self.phi)
        except AttributeError:
            return None

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
        if value not in [None, ""]:
            value = int(value)
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
            unit_moisture_volume = unit_moisture_weight / self.ulw
            saturation = unit_moisture_volume / self._calc_unit_void_volume()
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

    @plasticity_index.setter
    def plasticity_index(self, value):
        self._add_to_stack("plasticity_index", value)
        self._plasticity_index = value

    def _calc_void_ratio(self):
        try:
            return self.specific_gravity * self._uww / self.unit_dry_weight - 1
        except TypeError:
            pass
        try:
            return (self.specific_gravity * self._uww - self.unit_sat_weight) / (self.unit_sat_weight - self.liq_sg * self._uww)
        except TypeError:
            pass
        try:
            return self.e_max - self.relative_density * (self.e_max - self.e_min)
        except TypeError:
            return None

    def _calc_relative_density(self):
        try:
            return (self.e_max - self.e_curr) / (self.e_max - self.e_min)
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
    def _uww(self):
        """
        Unit water of reference water used to calculate specific gravity values
        :return:
        """
        return self.gravity * MASS_DENSITY_WATER

    @property
    def liq_sg(self):
        return self.liq_mass_density / MASS_DENSITY_WATER

    def _calc_specific_gravity(self):
        try:
            return (1 + self.e_curr) * self.unit_dry_weight / self._uww
        except TypeError:
            pass
        try:
            return (1 + self.e_curr) * self.unit_sat_weight / self._uww - self.e_curr * self.liq_sg
        except TypeError:
            return None

    def _calc_unit_dry_weight(self):
        try:
            return (self.specific_gravity * self._uww) / (1 + self.e_curr)  # dry relationship
        except TypeError:
            return None

    def _calc_unit_sat_weight(self):
        try:
            return ((self.specific_gravity + self.e_curr * self.liq_sg) * self._uww) / (1 + self.e_curr)
        except TypeError:
            return None

    def _calc_unit_moist_weight(self):
        try:
            return self._calc_unit_moisture_weight() + self.unit_dry_weight
        except TypeError:
            return None

    def _calc_saturation(self):
        try:
            unit_moisture_weight = self.unit_moist_weight - self.unit_dry_weight
            unit_moisture_volume = unit_moisture_weight / self.ulw
            return unit_moisture_volume / self._calc_unit_void_volume()
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
        f_map["_specific_gravity"] = self._calc_specific_gravity
        f_map["_unit_dry_weight"] = self._calc_unit_dry_weight
        f_map["_unit_sat_weight"] = self._calc_unit_sat_weight
        # saturation
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
                    #raise ModelError("new %s is inconsistent with current value (%.3f, %.3f)" % (item, curr_value,
                     #                                                                                      value))
                    raise ModelError(f"new {item} is inconsistent with current value ({curr_value}, {value})")
                setattr(self, item, value)

    def _calc_unit_void_volume(self):
        """Return the volume of the voids for total volume equal to a unit"""
        try:
            return self.e_curr / (1 + self.e_curr)
        except ValueError:
            return None

    def _calc_unit_solid_volume(self):
        """Return the volume of the solids for total volume equal to a unit"""
        try:
            return 1.0 - self._calc_unit_void_volume()
        except ValueError:
            return None

    def _calc_unit_moisture_weight(self):
        """Return the weight of the voids for total volume equal to a unit"""
        try:
            return self.saturation * self._calc_unit_void_volume() * self.ulw
        except ValueError:
            return None


class CriticalSoil(Soil):
    # critical state parameters
    e_cr0 = 0.0
    p_cr0 = 0.0
    lamb_crl = 0.0
    type = "critical_soil"

    def __init__(self, pw=9800, liq_mass_density=None, g=9.8,  **kwargs):
        # run parent class initialiser function
        super(CriticalSoil, self).__init__(pw=pw, liq_mass_density=liq_mass_density, g=g, **kwargs)
        self._extra_class_inputs = ["e_cr0", "p_cr0", "lamb_crl"]
        self.inputs = self.inputs + self._extra_class_inputs
        for param in kwargs:
            if param in self.inputs:
                setattr(self, param, kwargs[param])

    @property
    def ancestor_types(self):
        return super(CriticalSoil, self).ancestor_types + [self.type]

    def e_critical(self, p):
        p = float(p)
        return self.e_cr0 - self.lamb_crl * np.log(p / self.p_cr0)


class StressDependentSoil(Soil):
    _g0_mod = None
    _p_atm = 101000.0  # Pa
    type = "stress_dependent_soil"
    _a = 0.5  # stress factor
    _g_mod_p0 = 0.0  # shear modulus at zero confining stress

    def __init__(self, pw=9800, liq_mass_density=None, g=9.8, **kwargs):

        super(StressDependentSoil, self).__init__(pw=pw, liq_mass_density=liq_mass_density, g=g, **kwargs)
        self._extra_class_inputs = ["g0_mod", "p_atm", "a"]
        self.inputs = self.inputs + self._extra_class_inputs
        for param in kwargs:
            if param in self.inputs:
                setattr(self, param, kwargs[param])

    @property
    def ancestor_types(self):
        return super(StressDependentSoil, self).ancestor_types + [self.type]

    # @g_mod.setter
    # def g_mod(self, value):
    #     raise ValueError

    @property
    def g0_mod(self):
        return self._g0_mod

    @g0_mod.setter
    def g0_mod(self, value):
        value = clean_float(value)
        self._g0_mod = value
        if value is not None:
            self._add_to_stack("g0_mod", float(value))

    @property
    def a(self):
        return self._a

    @a.setter
    def a(self, value):
        value = clean_float(value)
        self._a = value
        if value is not None:
            self._add_to_stack("a", float(value))

    @property
    def g_mod_p0(self):
        return self._g_mod_p0

    @g_mod_p0.setter
    def g_mod_p0(self, value):
        value = clean_float(value)
        self._g_mod_p0 = value
        if value is not None:
            self._add_to_stack("g_mod_p0", float(value))

    @property
    def p_atm(self):
        return self._p_atm

    @p_atm.setter
    def p_atm(self, value):
        value = clean_float(value)
        self._p_atm = value
        if value is not None:
            self._add_to_stack("p_atm", float(value))

    def get_g_mod_at_v_eff_stress(self, v_eff_stress):
        k0 = 1 - np.sin(self.phi_r)
        return self.g0_mod * self.p_atm * (v_eff_stress * (1 + 2 * k0) / 3 / self.p_atm) ** self.a + self.g_mod_p0

    def set_g0_mod_at_v_eff_stress(self, v_eff_stress, g_mod, g_mod_p0=None):
        if g_mod_p0 is not None:
            self.g_mod_p0 = g_mod_p0
        k0 = 1 - np.sin(self.phi_r)
        m = self.p_atm * (v_eff_stress * (1 + 2 * k0) / 3 / self.p_atm) ** self.a
        self.g0_mod = (g_mod - self.g_mod_p0) / m

    def get_g_mod_at_m_eff_stress(self, m_eff_stress):
        return self.g0_mod * self.p_atm * (m_eff_stress / self.p_atm) ** self.a + self.g_mod_p0

    def set_g0_mod_at_m_eff_stress(self, m_eff_stress, g_mod, g_mod_p0=None):
        if g_mod_p0 is not None:
            self.g_mod_p0 = g_mod_p0
        m = self.p_atm * (m_eff_stress / self.p_atm) ** self.a
        self.g0_mod = (g_mod - self.g_mod_p0) / m

    def get_shear_vel_at_v_eff_stress(self, v_eff_stress, saturated):
        try:
            g_mod = self.get_g_mod_at_v_eff_stress(v_eff_stress)
            if saturated:
                return np.sqrt(g_mod / self.unit_sat_mass)
            else:
                return np.sqrt(g_mod / self.unit_dry_mass)
        except TypeError:
            return None

    def g_mod_at_v_eff_stress(self, v_eff_stress):
        deprecation("Use get_g_mod_at_v_eff_stress")
        return self.get_g_mod_at_v_eff_stress(v_eff_stress)

    def g_mod_at_m_eff_stress(self, m_eff_stress):
        deprecation("Use get_g_mod_at_m_eff_stress")
        return self.get_g_mod_at_m_eff_stress(m_eff_stress)

    def calc_shear_vel_at_v_eff_stress(self, saturated, v_eff_stress):
        deprecation("Use get_shear_vel_at_v_eff_stress - note inputs switched")
        return self.get_shear_vel_at_v_eff_stress(v_eff_stress, saturated)


class SoilLayer(Soil):  # not used

    def __init__(self, depth=0.0, height=1000, top_total_stress=0.0, top_pore_pressure=0.0):
        super(SoilLayer, self).__init__()
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
    hydrostatic = False
    base_type = "soil_profile"
    type = "soil_profile"

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
        self._layers = OrderedDict([(0.0, Soil())])  # [depth to top of layer, Soil object]
        self.skip_list = ["layers"]
        self.split = OrderedDict()

    def __str__(self):
        return "SoilProfile id: {0}, name: {1}".format(self.id, self.name)

    def add_to_dict(self, models_dict, **kwargs):
        if self.base_type not in models_dict:
            models_dict[self.base_type] = OrderedDict()
        if "soil" not in models_dict:
            models_dict["soil"] = OrderedDict()
        profile_dict = self.to_dict(**kwargs)
        profile_dict["layers"] = []
        for layer in self.layers:
            models_dict["soil"][self.layers[layer].unique_hash] = self.layers[layer].to_dict(**kwargs)
            profile_dict["layers"].append({
                "soil_id": str(self.layers[layer].id),
                "soil_unique_hash": str(self.layers[layer].unique_hash),
                "depth": float(layer)
            })
        models_dict["soil_profile"][self.unique_hash] = profile_dict

    @property
    def ancestor_types(self):
        return super(SoilProfile, self).ancestor_types + ["soil_profile"]

    def add_layer(self, depth, soil):
        """
        Adds a soil to the SoilProfile at a set depth.

        Note, the soils are automatically reordered based on depth from surface.

        :param depth: depth from surface to top of soil layer
        :param soil: Soil object
        """

        self._layers[depth] = soil
        self._sort_layers()
        if self.hydrostatic:
            if depth >= self.gwl:
                soil.saturation = 1.0
            else:
                li = self.get_layer_index_by_depth(depth)
                layer_height = self.get_layer_height(li)
                if layer_height is None:
                    soil.saturation = 0.0
                elif depth + layer_height <= self.gwl:
                    soil.saturation = 0.0
                else:
                    sat_height = depth + self.get_layer_height(li) - self.gwl
                    soil.saturation = sat_height / self.get_layer_height(li)

    def _sort_layers(self):
        """Sort the layers by depth."""
        self._layers = OrderedDict(sorted(self._layers.items(), key=lambda t: t[0]))

    @property
    def id(self):
        """Get the id number of the soil profile"""
        return self._id

    @id.setter
    def id(self, value):
        """
        Set the id of the soil profile

        :param value: int
        :return:
        """
        self._id = int(value)

    @property
    def gwl(self):
        """Get the ground water level"""
        return self._gwl

    @gwl.setter
    def gwl(self, value):
        """
        Set the depth from the surface to the ground water level (gwl)

        :param value:
        :return:
        """
        self._gwl = float(value)

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        """
        Sets the depth from the surface to the base of the soil profile

        :param value: float, height
        :return:
        """
        self._height = float(value)

    def get_layer_height(self, layer_int):
        """
        Get the layer height by layer id number.

        :param layer_int:
        :return: float, height of the soil layer
        """
        if layer_int == self.n_layers:
            if self.height is None:
                return None
            return self.height - self.get_layer_depth(layer_int)
        else:
            return self.get_layer_depth(layer_int + 1) - self.get_layer_depth(layer_int)

    def layer_height(self, layer_int):
        return self.get_layer_height(layer_int)

    def get_layer_depth(self, layer_int):
        """
        Get the distance from the surface to the top of the layer by layer id number.

        :param layer_int: int,
            Layer index
        :return: float,
            Depth of the soil layer
        """
        layer_int = int(layer_int)
        try:
            return self.depths[layer_int - 1]
        except IndexError as e:
            if layer_int == 0 or layer_int > self.n_layers:
                raise IndexError("index={0}, but must be between 1 and {1}".format(layer_int, self.n_layers))
            else:
                raise e

    def layer_depth(self, index):
        return self.get_layer_depth(index)

    def get_layer_mid_depth(self, layer_int):
        """
        Get the distance from the surface to the centre of the layer by layer id number.

        :param layer_int: int,
            Layer index
        :return: float,
            Depth to middle of the soil layer
        """
        return self.get_layer_depth(layer_int) + self.get_layer_height(layer_int) / 2

    @property
    def layers(self):
        return self._layers

    @property
    def layer_objects(self):
        return list(self._layers.values())

    @layers.setter
    def layers(self, layers):
        for layer in layers:
            layer_depth = layer["depth"]
            sl = layer["soil"]  # is actually a soil object
            self.add_layer(layer_depth, sl)

    def remove_layer_at_depth(self, depth):
        try:
            del self._layers[depth]
        except KeyError:
            raise KeyError("Depth: {0} not found in {1}".format(depth, list(self.layers.keys())))

    def remove_layer(self, layer_int):
        key = list(self._layers.keys())[layer_int - 1]
        del self._layers[key]

    def replace_layer(self, layer_int, soil):
        key = list(self._layers.keys())[layer_int - 1]
        self._layers[key] = soil

    def layer(self, index):
        index = int(index)
        if index == 0:
            raise KeyError("index=%i, but must be 1 or greater." % index)
        return list(self._layers.values())[index - 1]

    def set_soil_ids_to_layers(self):
        for i in range(1, len(self._layers) + 1):
            self.layer(i).id = i

    def get_layer_index_by_depth(self, depth):
        for i, ld in enumerate(self.layers):
            if ld > depth:
                return i
        return self.n_layers

    def get_soil_at_depth(self, depth):
        lay_index = self.get_layer_index_by_depth(depth)
        return self.layer(lay_index)

    def get_parameter_at_depth(self, depth, parameter):
        lay_index = self.get_layer_index_by_depth(depth)
        soil = self.layer(lay_index)
        if hasattr(soil, parameter):
            return getattr(soil, parameter)
        else:
            raise ModelError("%s not in soil object at depth (%.3f)." % (parameter, depth))

    def get_parameters_at_depth(self, depth, parameters):
        lay_index = self.get_layer_index_by_depth(depth)
        soil = self.layer(lay_index)
        od = OrderedDict()
        for parameter in parameters:
            if hasattr(soil, parameter):
                od[parameter] = getattr(soil, parameter)
        return od
    
    def get_parameters_at_depths(self, depths, parameters):
        od = OrderedDict()
        for parameter in parameters:
            od[parameter] = []
        for depth in depths:
            lay_index = self.get_layer_index_by_depth(depth)
            soil = self.layer(lay_index)
            
            for parameter in parameters:
                if hasattr(soil, parameter):
                    od[parameter].append(getattr(soil, parameter))
            return od

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

    # def set_soil_saturation_based_on_gwl(self):
    #     for depth in self._layers:
    #         if depth

    def vertical_total_stress(self, y_c):
        deprecation("Use get_v_total_stress_at_depth")
        return self.get_v_total_stress_at_depth(y_c)

    def get_v_total_stress_at_depth(self, z):
        """
        Determine the vertical total stress at depth z, where z can be a number or an array of numbers.
        """

        if not hasattr(z, "__len__"):
            return self.one_vertical_total_stress(z)
        else:
            sigma_v_effs = []
            for value in z:
                sigma_v_effs.append(self.one_vertical_total_stress(value))
            return np.array(sigma_v_effs)

    def one_vertical_total_stress(self, z_c):
        """
        Determine the vertical total stress at a single depth z_c.

        :param z_c: depth from surface
        """
        if self.gwl < 0:
            total_stress = -self.gwl * self.unit_water_weight
        else:
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
                    total_stress += height * self.layer(layer_int).get_unit_weight_or('dry')
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

        :param y_c: float, depth from surface
        """
        deprecation("Use get_hydrostatic_pressure_at_depth")
        return self.get_hydrostatic_pressure_at_depth(y_c)

    def get_hydrostatic_pressure_at_depth(self, y_c):
        return np.where(y_c < self.gwl, 0.0, (y_c - self.gwl) * self.unit_water_weight)

    def vert_eff_stress(self, y_c):
        """
        Determine the vertical effective stress at a single depth z_c.

        :param y_c: float, depth from surface
        """
        deprecation("Use get_v_eff_stress_at_depth")
        return self.get_v_eff_stress_at_depth(y_c)

    def get_v_eff_stress_at_depth(self, y_c):
        """
        Determine the vertical effective stress at a single depth z_c.

        :param y_c: float, depth from surface
        """
        sigma_v_c = self.get_v_total_stress_at_depth(y_c)
        pp = self.get_hydrostatic_pressure_at_depth(y_c)
        sigma_veff_c = sigma_v_c - pp
        return sigma_veff_c

    def vertical_effective_stress(self, y_c):  # deprecated function
        """Deprecated. Use get_vert_eff_stress"""
        deprecation("Use get_v_eff_stress_at_depth")
        return self.get_v_eff_stress_at_depth(y_c)

    def get_shear_vel_at_depth(self, y_c):
        """
        Get the shear wave velocity at a depth.

        :param y_c: float, depth from surface
        :return:
        """
        sl = self.get_soil_at_depth(y_c)
        if y_c <= self.gwl:
            saturation = False
        else:
            saturation = True
        if hasattr(sl, "get_shear_vel_at_v_eff_stress"):
            v_eff = self.get_v_eff_stress_at_depth(y_c)
            vs = sl.get_shear_vel_at_v_eff_stress(v_eff, saturation)
        else:
            vs = sl.get_shear_vel(saturation)
        return vs

    def shear_vel_at_depth(self, y_c):
        deprecation("Use get_shear_vel_at_depth")
        return self.get_shear_vel_at_depth(y_c)

    def split_props(self, incs=None, target=1.0, props=None):
        deprecation('Use gen_split')
        self.gen_split(incs=incs, target=target, props=props)

    def gen_split(self, incs=None, target=1.0, props=None, pos='centre'):
        if incs is None:
            incs = np.ones(self.n_layers) * target
        if props is None:
            props = ['unit_mass', 'shear_vel']
        else:
            if 'thickness' in props:
                props.remove('thickness')
        dd = OrderedDict([('thickness', []), ('depth', [])])
        for item in props:
            dd[item] = []

        cum_thickness = 0
        for i in range(self.n_layers):
            sl = self.layer(i + 1)
            thickness = self.get_layer_height(i + 1)
            if thickness is None:
                raise ValueError("thickness of layer {0} is None, check if soil_profile.height is set".format(i + 1))
            if thickness <= 0:  # below soil profile height
                continue
            n_slices = max(int(thickness / incs[i]), 1)
            slice_thickness = float(thickness) / n_slices
            for j in range(n_slices):
                dd["thickness"].append(slice_thickness)
                v_eff = None
                if pos == 'centre':
                    centre_depth = cum_thickness + slice_thickness * 0.5
                elif pos == 'bottom':
                    centre_depth = cum_thickness + slice_thickness
                else:
                    centre_depth = cum_thickness
                dd['depth'].append(centre_depth)
                cum_thickness += slice_thickness
                if centre_depth > self.gwl:
                    saturated = True
                else:
                    saturated = False
                # some properties require vertical effective stress or saturation
                for item in props:
                    value = None
                    fn0 = "get_{0}_at_v_eff_stress".format(item)  # first check for stress dependence
                    fn1 = "get_{0}".format(item)  # first check for stress dependence
                    if hasattr(sl, fn0):
                        try:
                            v_eff = self.get_v_eff_stress_at_depth(centre_depth)
                        except TypeError:
                            raise ValueError("Cannot compute vertical effective stress at depth: {0}".format(centre_depth))
                        value = sf.get_value_of_a_get_method(sl, fn0, extras={"saturated": saturated,
                                                                              'v_eff_stress': v_eff})
                    elif hasattr(sl, fn1):
                        value = sf.get_value_of_a_get_method(sl, fn1, extras={"saturated": saturated})
                    elif hasattr(sl, item):
                        value = getattr(sl, item)

                    dd[item].append(value)

        for item in dd:
            dd[item] = np.array(dd[item])
        self.split = dd


def discretize_soil_profile(sp, incs=None, target=1.0):
    """
    Splits the soil profile into slices and stores as dictionary

    :param sp: SoilProfile
    :param incs: array_like, increments of depth to use for each layer
    :param target: target depth increment size
    :return: dict
    """

    if incs is None:
        incs = np.ones(sp.n_layers) * target
    dd = {}
    dd["thickness"] = []
    dd["unit_mass"] = []
    dd["shear_vel"] = []
    cum_thickness = 0
    for i in range(sp.n_layers):
        sl = sp.layer(i + 1)
        thickness = sp.get_layer_height(i + 1)
        n_slices = max(int(thickness / incs[i]), 1)
        slice_thickness = float(thickness) / n_slices
        for j in range(n_slices):
            cum_thickness += slice_thickness
            if cum_thickness >= sp.gwl:
                rho = sl.unit_sat_mass
                saturation = True
            else:
                rho = sl.unit_dry_mass
                saturation = False
            if hasattr(sl, "get_shear_vel_at_v_eff_stress"):
                v_eff = sp.vertical_effective_stress(cum_thickness)
                vs = sl.get_shear_vel_at_v_eff_stress(v_eff, saturation)
            else:
                vs = sl.get_shear_vel(saturation)
            dd["shear_vel"].append(vs)
            dd["unit_mass"].append(rho)
            dd["thickness"].append(slice_thickness)
    for item in dd:
        dd[item] = np.array(dd[item])
    return dd


# TODO: extend to have LiquefiableSoil


class SoilCritical(CriticalSoil):
    def __init__(self, pw=9800):
        """Deprecated. Use CriticalSoil"""
        deprecation("SoilCritical class is deprecated (remove in version 1.0), use CriticalSoil.")
        super(SoilCritical, self).__init__(pw=pw)


class SoilStressDependent(StressDependentSoil):
    def __init__(self, pw=9800):
        """Deprecated. Use StressDependentSoil"""
        deprecation("SoilStressDependent class is deprecated (remove in version 1.0), use StressDependentSoil.")
        super(SoilStressDependent, self).__init__(pw=pw)
