__author__ = 'maximmillen'

from sfsimodels.checking_tools import isclose
from sfsimodels.models.material import Concrete


def test_youngs():
    concrete = Concrete()
    assert isclose(concrete.youngs_concrete, 25084388909.2, 0.0001)


def can_iterate():
    concrete = Concrete()
    print(concrete.attributes)
    for item in concrete:
        print(item)

if __name__ == '__main__':
    can_iterate()