import math
import numbers
from collections import OrderedDict

import numpy as np

from sfsimodels.exceptions import ModelError
from sfsimodels.models.abstract_models import PhysicalObject


class Soil(PhysicalObject):
    g_mod = 0.0  # Shear modulus [Pa]
    phi = 0.0  # Critical friction angle [degrees]
    relative_density = 0.0  # [decimal]
    unit_dry_weight = None  # N/m3
    unit_sat_weight = None  # TODO: use specific gravity and void ratio
    cohesion = 0.0  # [Pa]
    poissons_ratio = 0.0
    e_min = 0.0
    e_max = 0.0
    e_cr0 = 0.0
    p_cr0 = 0.0
    lamb_crl = 0.0
    saturation = 0.0

    # Calculated values
    phi_r = None
    e_initial = None
    k_0 = None

    inputs = [
        "g_mod",
        "phi",
        "relative_density",
        "unit_dry_weight",
        "unit_sat_weight",
        "cohesion",
        "poissons_ratio",
        "e_min",
        "e_max",
        "e_cr0",
        "p_cr0",
        "lamb_crl"
    ]

    @property
    def unit_weight(self):
        if self.saturation:
            return self.unit_sat_weight
        else:
            return self.unit_dry_weight

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
    def n1_60(self):
        return (self.relative_density * 100. / 15) ** 2


class SoilProfile(PhysicalObject):
    """
    An object to describe a soil profile
    """

    gwl = None  # Ground water level [m]
    unit_weight_water = 9800.  # [N/m3]

    inputs = [
        "gwl",
        "unit_weight_water",
        "layers"
    ]

    def __init__(self):
        super(PhysicalObject, self).__init__()  # run parent class initialiser function
        self._layers = OrderedDict([(0, Soil())])  # [depth to top of layer, Soil object]

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
    def layers(self):
        return self._layers

    def remove_layer(self, depth):
        del self._layers[depth]

    def layer(self, index):
        return list(self._layers.values())[index]

    def layer_depth(self, index):
        return self.depths[index]

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

