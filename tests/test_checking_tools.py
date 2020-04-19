from sfsimodels import checking_tools as ct
import sfsimodels as sm


def test_isclose():
    assert not ct.isclose(1, None)
    assert not ct.isclose(1, 2)
    assert not ct.isclose(0, 1)
    assert ct.isclose(0, 0)
    assert ct.isclose(0.00, 0.00)
    assert ct.isclose(1.1, 1., rel_tol=1.2)
    assert ct.isclose(1.1, 1., abs_tol=0.2)


def test_assign_for_zero():
    sl = sm.Soil()
    sl.poissons_ratio = 0.0
    sl.phi = 35.0
    sl.unit_dry_weight = 2.202e3 * 9.8
    vs = 160.232334342343423
    sl.unit_dry_weight = 2.202e3 * 9.8
    sl.g_mod = vs ** 2 * sl.unit_dry_mass


if __name__ == '__main__':
    test_assign_for_zero()
