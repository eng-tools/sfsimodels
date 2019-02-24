import numpy as np
from sfsimodels.models.material import Concrete


def test_youngs():
    concrete = Concrete()
    assert np.isclose(concrete.youngs_concrete, 25084388909.2, rtol=0.0001)


def can_iterate():
    concrete = Concrete()
    for item in concrete:
        pass


if __name__ == '__main__':
    can_iterate()
