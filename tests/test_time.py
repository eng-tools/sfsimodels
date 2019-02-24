import numpy as np

from sfsimodels.models import time


def test_time_series():
    values = np.linspace(0, 10, 101)
    dt = 0.5
    ts = time.TimeSeries(values, dt)
    assert ts.npts == 101
    assert ts.dt == 0.5
    assert len(ts.time) == len(values)
    assert np.isclose(ts.time[4], 2.0)
    assert np.isclose(ts.time[-1], 50.0)


def test_time_indices():
    npts = 1000
    dt = 0.5
    start = 0
    end = 10
    index = False
    s_index, e_index = time.time_indices(npts, dt, start, end, index)
    assert s_index == 0
    assert e_index == 21

    start = 2
    s_index, e_index = time.time_indices(npts, dt, start, end, index)
    assert s_index == 4
    assert e_index == 21

    index = True
    s_index, e_index = time.time_indices(npts, dt, start, end, index)
    assert s_index == 2
    assert e_index == 10


if __name__ == '__main__':
    test_time_series()
