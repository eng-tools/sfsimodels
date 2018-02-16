import numpy as np

from sfsimodels import exceptions


class TimeSeries(object):
    _npts = None

    def __init__(self, values, dt, name="unnamed"):
        """
        A sequence of values recorded at equal time steps.

        :param values: A sequence of values recorded at equal time steps.
        :param dt: time step
        """
        self.stype = "time_series"
        self._dt = dt
        self._values = values
        self.name = name
        self.reassess()

    def reassess(self):
        """
        re-computes dynamic properties
        :return:
        """
        self._npts = len(self.values)

    @property
    def values(self):
        return self._values

    @property
    def dt(self):
        """ The time step """
        return self._dt

    @property
    def npts(self):  # Deliberately no public setter method for this
        """ The number of points in the time series """
        return self._npts

    @values.setter
    def values(self, series):
        """ The values in the time series """
        self._values = np.array(series)

    @property
    def time(self):
        """ An array of time of equal length to the time series """
        return np.arange(0, self.npts) * self.dt

    def cut(self, start=0, end=-1, index=False):
        """
        The method cuts the time series to reduce its length.
        :param start: int or float, optional, New start point
        :param end: int or float, optional, New end point
        :param index: bool, optional, if False then start and end are considered values in time.
        """
        s_index, e_index = time_indices(self.npts, self.dt, start, end, index)
        self._values = np.array(self.values[s_index:e_index])


def time_indices(npts, dt, start, end, index):
    """
    Determine the new start and end indices of the time series.

    :param npts: Number of points in original time series
    :param dt: Time step of original time series
    :param start: int or float, optional, New start point
    :param end: int or float, optional, New end point
    :param index: bool, optional, if False then start and end are considered values in time.
    :return: tuple, start index, end index
    """
    if index is False:  # Convert time values into indices
        if end != -1:
            e_index = int(end / dt) + 1
        else:
            e_index = end
        s_index = int(start / dt)
    else:
        s_index = start
        e_index = end
    if e_index > npts:
        raise exceptions.ModelWarning("Cut point is greater than time series length")
    return s_index, e_index
