import math
import numbers
import numpy as np

__author__ = 'maximmillen'


class Soil(object):
    G_mod = None
    phi = None
    relative_density = None
    height_crust = None
    height_liq = None
    gwl = None
    unit_weight_crust = None
    unit_sat_weight_liq = None  # TODO: use specific gravity and void ratio
    unit_weight_water = 9.8
    crust_cohesion = None
    crust_phi = None
    poissons_ratio = None
    e_min = None
    e_max = None
    e_cr0 = None
    p_cr0 = None
    lamb_crl = None
    clay_crust = True  # deprecated

    inputs = [
        "G_mod",
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
        :param sp:
        :param crust_phi:
        :return:
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


class Hazard(object):
    z_factor = None
    r_factor = 1.0
    n_factor = 1.0
    magnitude = None
    corner_period = None
    corner_acc_factor = None

    inputs = [
        "z_factor",
        "r_factor",
        "n_factor",
        "magnitude",
        "corner_period",
        "corner_acc_factor"
    ]

    # Calculated values
    pga = None
    corner_acc = None
    corner_disp = None

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


class Foundation(object):
    width = None
    length = None
    depth = None

    inputs = [
        "width",
        "length",
        "depth"
    ]

    @property
    def i_ww(self):
        return self.width * self.length ** 3 / 12

    @property
    def i_ll(self):
        return self.length ** 3 * self.width / 12


class Structure(object):
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


class SoilStructureSystem(object):
    bd = Structure()
    fd = Foundation()
    sp = Soil()
    hz = Hazard()
    name = "Nameless"

    inputs = [
        "name"
    ]
