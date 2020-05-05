from sfsimodels.models.base_model import BaseECPModel


class Coords(BaseECPModel):
    """
    An object to describe loads along axes
    """
    _id = None
    name = None

    base_type = "coords"
    type = "coords"

    _extra_class_inputs = [
        "x",
        "y",
        "z",
    ]

    def __str__(self):
        return f"Coords ({self.c})"

    def __format__(self, format_spec):
        return f"Coords ({self.c})"

    def __init__(self, x=None, y=None, z=None):
        self.x = x  # [m]
        self.y = y  # [m]
        self.z = z  # [m]
        self.inputs = [
            "id",
            "name",
            "base_type",
            "type",
            ] + self._extra_class_inputs

    @property
    def ancestor_types(self):
        return ["coords"]

    @property
    def c(self):
        return tuple([self.x, self.y, self.z])

    @c.setter
    def c(self, values):
        self.x = values[0]
        self.y = values[1]
        self.z = values[2]


class GlobalCoords(Coords):
    type = "global_coords"

    def __init__(self, x=None, y=None, z=None):
        super(GlobalCoords, self).__init__(x=x, y=y, z=z)

    def __str__(self):
        return "GlobalCoords"

    def __format__(self, format_spec):
        return "GlobalCoords"

    @property
    def ancestor_types(self):
        return super(GlobalCoords, self).ancestor_types + ["global_coords"]


class PositionalCoords(Coords):
    type = "global_coords"

    def __init__(self, x=None, y=None, z=None, obj=None):
        super(PositionalCoords, self).__init__(x=x, y=y, z=z)
        self.obj = obj

    def __str__(self):
        return "GlobalCoords"

    def __format__(self, format_spec):
        return "GlobalCoords"

    @property
    def ancestor_types(self):
        return super(PositionalCoords, self).ancestor_types + ["positional_coords"]
