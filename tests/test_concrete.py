import numpy as np
from sfsimodels.models.materials import ReinforcedConcreteMaterial


def test_youngs():
    concrete = ReinforcedConcreteMaterial()
    assert np.isclose(concrete.e_mod_conc, 25084388909.2, rtol=0.0001)


def can_iterate():
    concrete = ReinforcedConcreteMaterial()
    for item in concrete:
        pass


if __name__ == '__main__':
    can_iterate()
