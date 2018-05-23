import numpy as np


def peak_friction_angle_bjerrum_1961(porosity):
    """
    See https://link.springer.com/content/pdf/10.1007%2F978-1-4020-8684-7.pdf
    Eq. 2.5

    :param porosity:
    :return:
    """
    return 12. + np.sqrt(27. ** 2 - ((27. / 11.5) * (porosity - .36)) ** 2)


def peak_friction_angle_peak_et_al_1974(spt_blow_count):
    """
    See https://link.springer.com/content/pdf/10.1007%2F978-1-4020-8684-7.pdf
    Eq. 2.6
    :param spt_blow_count:
    :return:
    """
    return 30. + 10. / 35 * (spt_blow_count - 10)


def n1_60(sl):
    """ Compute the normalised SPT blow count"""
    return (sl.relative_density * 100. / 15) ** 2
