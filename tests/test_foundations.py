from sfsimodels import models
from sfsimodels.checking_tools import isclose


def test_raft_foundation():
    fd = models.FoundationRaft()
    fd.length = 4
    fd.width = 6
    assert fd.area == 24
    fd.height = 0.1
    fd.density = 3
    expected_mass = fd.length * fd.width * fd.height * fd.density
    assert isclose(expected_mass, 7.2, rel_tol=0.0001)
    assert isclose(fd.mass, expected_mass, rel_tol=0.0001)
    i_ll = fd.width ** 3 * fd.length / 12
    i_ww = fd.length ** 3 * fd.width / 12
    assert isclose(fd.i_ll, i_ll, rel_tol=0.001)
    assert isclose(fd.i_ww, i_ww, rel_tol=0.001)


def test_pad_foundation():
    fd = models.FoundationPad()
    fd.length = 15
    fd.pad_length = 3
    fd.n_pads_l = 4
    assert fd.pad_position_l(2) == 9.5
    fd.width = 11
    fd.pad_width = 2
    fd.n_pads_w = 4
    assert fd.pad_position_w(1) == 4.0
    assert fd.pad_i_ww == 3. ** 3 * 2 / 12
    assert fd.pad_i_ll == 2. ** 3 * 3 / 12
    assert fd.pad_area == 2 * 3
    assert isclose(fd.i_ww, 1992.0, rel_tol=0.001)
    assert isclose(fd.i_ll, 1112.0, rel_tol=0.001)
    assert fd.area == 4 * 4 * 2 * 3


def test_pad_density_setter():
    fd = models.FoundationPad()
    fd.length = 15
    fd.pad_length = 3
    fd.n_pads_l = 2
    fd.width = 11
    fd.pad_width = 2
    fd.n_pads_w = 2
    assert fd.mass is None
    fd.height = 0.5
    assert fd.mass is None
    fd.density = 3
    expected_area = (2 * 2) * (3 * 2)
    assert fd.area == expected_area
    expected_mass = expected_area * 0.5 * 3
    assert isclose(fd.mass, expected_mass, rel_tol=0.0001)


def test_zero_height_raft():
    fd = models.FoundationRaft()
    fd.length = 4
    fd.width = 6
    fd.height = 0.0
    fd.density = 3
    assert isclose(fd.mass, 0.0, rel_tol=0.0001)
    fd2 = models.FoundationRaft()
    fd2.length = 4
    fd2.width = 6
    fd2.height = 0.0
    fd2.mass = 3
    assert fd2.density is None


def test_load_nan():
    fd = models.FoundationRaft()
    fd.g_mod = ""
    fd.bulk_mod = ""
    fd.g_mod = None
    for item in fd.inputs:
        setattr(fd, item, "")
        setattr(fd, item, None)

    pd = models.FoundationPad()
    pd.g_mod = ""
    pd.bulk_mod = ""
    pd.g_mod = None
    for item in pd.inputs:
        setattr(pd, item, "")
        setattr(pd, item, None)


if __name__ == '__main__':
    test_load_nan()
