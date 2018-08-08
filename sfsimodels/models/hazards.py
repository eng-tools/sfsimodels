import math
from sfsimodels.models.abstract_models import PhysicalObject


class SeismicHazard(PhysicalObject):
    """
    An object to describe seismic hazard.
    """
    z_factor = 0.0
    r_factor = 1.0
    n_factor = 1.0
    magnitude = 0.0
    corner_period = -1.0
    corner_acc_factor = 0.0
    site_class = None
    type = "seismic_hazard"

    inputs = [
        "z_factor",
        "r_factor",
        "n_factor",
        "magnitude",
        "site_class",
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
    def ancestor_types(self):
        return super(SeismicHazard, self).ancestor_types + [self.type]

    @property
    def pga(self):
        return self.z_factor * self.r_factor * self.n_factor

    @property
    def corner_acc(self):
        return self.corner_acc_factor * self.z_factor * self.r_factor * self.n_factor * 9.8

    @property
    def corner_disp(self):
        return self.corner_acc / (2 * math.pi / self.corner_period) ** 2


def msf(magnitude):
    """
    Magnitude scaling factor

    :param magnitude: Earthquake moment magnitude
    :return: float
    """
    magnitude_sf = 10. ** 2.24 / magnitude ** 2.56
    return magnitude_sf

# def define_hazard_by_code(self, z_factor, r_factor, n_factor, site_class="C", code="NZS"):
#     pass