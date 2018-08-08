import numpy as np
from sfsimodels.models.abstract_models import PhysicalObject

__author__ = 'maximmillen'


class Concrete(PhysicalObject):
    """
    An object to describe reinforced concrete
    """
    base_type = "material"  # not actually available
    type = "concrete"

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