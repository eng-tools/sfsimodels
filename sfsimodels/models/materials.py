import numpy as np
from sfsimodels.models.abstract_models import PhysicalObject

__author__ = 'maximmillen'


class ReinforcedConcreteMaterial(PhysicalObject):
    """
    An object to describe reinforced concrete
    """
    base_type = "material"  # not actually available
    type = "rc_material"

    def __init__(self, fc=30.0e6, fy=300.0e6, e_mod_steel=200e9, poissons_ratio=0.18):
        self.fc = fc  # Pa
        self.fy = fy  # Pa
        self.e_mod_steel = e_mod_steel  # Pa
        self.poissons_ratio = poissons_ratio

    inputs = [
        'base_type',
        'type',
        'fc',
        'fy',
        'e_mod_steel',
        'poissons_ratio'
    ]

    @property
    def e_mod_conc(self):
        if self.fc is not None:
            return (3320 * np.sqrt(self.fc / 1e6) + 6900.0) * 1e6
        return None


class Concrete(ReinforcedConcreteMaterial):
    pass


if __name__ == '__main__':
    rc = ReinforcedConcreteMaterial()
    print(rc.e_mod_conc)