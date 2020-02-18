from sfsimodels import functions as fns
import pytest
import numpy as np


def test_interp_left():
    x0 = [0, 1, 5]
    x = [0, 2, 6]
    y = [1.5, 2.5, 3.5]
    y_new = fns.interp_left(x0, x, y)
    expected = np.array([1.5, 1.5, 2.5])
    assert np.isclose(y_new, expected).all(), y_new

    x0 = [0, 2, 6]
    y_new = fns.interp_left(x0, x, y)
    expected = np.array([1.5, 2.5, 3.5])
    assert np.isclose(y_new, expected).all(), y_new
    x0 = [-1, 2, 6]
    with pytest.raises(AssertionError):
        y_new = fns.interp_left(x0, x, y)
