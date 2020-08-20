from sfsimodels.models.abstract_models import PhysicalObject


class Section(PhysicalObject):
    id = None
    type = "section"
    base_type = "section"
    _depth = None
    _width = None

    def __init__(self):
        self.inputs = ["depth",
                       "width",
                       ]

    @property
    def depth(self):
        return self._depth

    @depth.setter
    def depth(self, value):
        self._depth = value

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        self._width = value

    @property
    def i_rot_ww(self):
        return self._width * self._depth ** 3 / 12

    @property
    def i_rot_dd(self):
        return self._width ** 3 * self._depth / 12


class RCBeamSection(Section):
    id = None
    type = "rc_section"
    base_type = "section"
    cracked_ratio = None
    _moment_cracked = None
    _moment_yield = None
    _moment_ult = None
    rc_mat = None

    @property
    def i_rot_ww_cracked(self):
        return self.cracked_ratio * self.i_rot_ww

    @property
    def i_rot_dd_cracked(self):
        return self.cracked_ratio * self.i_rot_dd

    @property
    def moment_cracked(self):
        return self._moment_cracked

    @moment_cracked.setter
    def moment_cracked(self, value):
        self._moment_cracked = value

    @property
    def moment_yield(self):
        return self._moment_yield

    @moment_yield.setter
    def moment_yield(self, value):
        self._moment_yield = value

    @property
    def moment_ult(self):
        return self._moment_ult

    @moment_ult.setter
    def moment_ult(self, value):
        self._moment_ult = value

    @property
    def e_mod_conc(self):
        return self.rc_mat.e_mod_conc


# class DetailedRCBeamSection(RCBeamSection):
#     pass  # define locate and type of all reinforcing

# class SimpleRCBeamSection(RCBeamSection):
#     _area_tension_steel = None
#
#     @property
#     def area_tension_steel(self):
#         return self._area_tension_steel
#
#     @area_tension_steel.setter
#     def area_tension_steel(self, value):
#         self._area_tension_steel = value

