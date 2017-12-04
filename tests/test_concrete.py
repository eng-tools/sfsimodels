__author__ = 'maximmillen'

from sfsimodels.models import Concrete


def test_youngs():
    concrete = Concrete()
    assert concrete.youngs_concrete == 25084388909.2


def can_iterate():
    concrete = Concrete()
    print(concrete.attributes)
    for item in concrete:
        print(item)

if __name__ == '__main__':
    can_iterate()