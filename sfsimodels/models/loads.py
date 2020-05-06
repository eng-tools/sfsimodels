from sfsimodels.models.abstract_models import PhysicalObject
from sfsimodels.models.coordinates import Coords


class Load(PhysicalObject):
    """
    An object to describe loads along axes
    """
    _id = None
    name = None

    base_type = "load"
    type = "load"

    _extra_class_inputs = [
        "p_x",
        "p_y",
        "p_z",
        "t_xx",
        "t_yy",
        "t_zz",
    ]

    def __str__(self):
        return f"Load id: {self.vector}, name: {1}"

    def __format__(self, format_spec):
        return "Load"

    def __init__(self, p_x=None, p_y=None, p_z=None, t_xx=None, t_yy=None, t_zz=None, surrogate=True):
        self._p_x = p_x  # [N], Load along the x-axis
        self._p_y = p_y  # [N], Load along the y-axis
        self._p_z = p_z  # [N], Load along the z-axis
        self._t_xx = t_xx  # [Nm], Torque applied around x-axis
        self._t_yy = t_yy  # [Nm], Torque applied around y-axis
        self._t_zz = t_zz  # [Nm], Torque applied around z-axis
        self.surrogate = surrogate  # if true the export as own object in ecp file
        self.inputs = [
            "id",
            "name",
            "base_type",
            "type",
            ] + self._extra_class_inputs

    @property
    def ancestor_types(self):
        return ["load_on_axes"]

    @property
    def p_x(self):
        return self._p_x

    @p_x.setter
    def p_x(self, value):
        self._p_x = value

    @property
    def p_y(self):
        return self._p_y

    @p_y.setter
    def p_y(self, value):
        self._p_y = value

    @property
    def p_z(self):
        return self._p_z

    @p_z.setter
    def p_z(self, value):
        self._p_z = value

    @property
    def t_xx(self):
        return self._t_xx

    @t_xx.setter
    def t_xx(self, value):
        self._t_xx = value

    @property
    def t_yy(self):
        return self._t_yy

    @t_yy.setter
    def t_yy(self, value):
        self._t_yy = value

    @property
    def t_zz(self):
        return self._t_zz

    @t_zz.setter
    def t_zz(self, value):
        self._t_zz = value

    @property
    def vector(self):
        return [self.p_x, self.p_y, self.p_z, self.t_xx, self.t_yy, self.t_zz]


class LoadAtCoords(Coords, Load):
    type = 'load_at_coords'

    def __init__(self, x=None, y=None, z=None, p_x=None, p_y=None, p_z=None, t_xx=None, t_yy=None, t_zz=None):
        Coords.__init__(self, x, y, z)
        Load.__init__(self, p_x=p_x, p_y=p_y, p_z=p_z, t_xx=t_xx, t_yy=t_yy, t_zz=t_zz)

    def __str__(self):
        return f"LoadAtCoords ({self.c}) ({self.vector})"

    def __format__(self, format_spec):
        return f"LoadAtCoords ({self.c}) ({self.vector})"
