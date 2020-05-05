from sfsimodels.models.base_model import BaseECPModel


class Units(BaseECPModel):
    """
    An object to describe loads along axes
    """
    base_type = "units"
    type = "units"

    _extra_class_inputs = [
        "x",
        "y",
        "z",
    ]

    def __str__(self):
        return "Units"

    def __format__(self, format_spec):
        return "Units"

    def __init__(self, length=None, mass=None, time='s'):
        self.length = length
        self.mass = mass
        self.time = time
        self.inputs = [
            "id",
            "name",
            "base_type",
            "type",
            ] + self._extra_class_inputs

    @property
    def ancestor_types(self):
        return ["units"]


class GlobalUnits(Units):  # If global units are set then
    type = "global_units"

    def __init__(self, length=None, mass=None, time='s'):
        super(GlobalUnits, self).__init__(length=length, mass=mass, time=time)

    def __str__(self):
        return "GlobalUnits"

    def __format__(self, format_spec):
        return "GlobalUnits"

    @property
    def ancestor_types(self):
        return super(GlobalUnits, self).ancestor_types + ["global_units"]
