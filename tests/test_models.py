from sfsimodels import models
from tests.checking_tools import isclose



def test_raft_foundation():
    fd = models.RaftFoundation()
    fd.length = 4
    fd.width = 6
    assert fd.area == 24
    fd.density = 3
    fd.height = 0.1
    assert isclose(fd.mass, 7.2, rel_tol=0.0001)
    i_ll = fd.width ** 3 * fd.length / 12
    i_ww = fd.length ** 3 * fd.width / 12
    assert isclose(fd.i_ll, i_ll, rel_tol=0.001)
    assert isclose(fd.i_ww, i_ww, rel_tol=0.001)


def test_pad_foundation():
    fd = models.PadFoundation()
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


if __name__ == '__main__':
    test_pad_foundation()
