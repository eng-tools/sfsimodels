from sfsimodels.models.abstract_models import PhysicalObject


class Section(PhysicalObject):
    id = None
    type = "section"
    base_type = "section"
    _depth = None
    _width = None
    _material = None
    loading_pre_reqs = ('material',)

    def __init__(self):
        self.inputs = [
            "base_type",
            "type",
            "depth",
            "width",
            "material"
                       ]
        self.skip_list = list(self.skip_list) + ['material']

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
    def mat(self):
        return self._material

    @property
    def material(self):
        return self._material

    @material.setter
    def material(self, value):
        self._material = value

    @mat.setter
    def mat(self, value):
        self._material = value

    @property
    def i_rot_ww(self):
        return self._width * self._depth ** 3 / 12

    @property
    def i_rot_dd(self):
        return self._width ** 3 * self._depth / 12

    def add_to_dict(self, models_dict, return_mdict=False, **kwargs):
        if self.base_type not in models_dict:
            models_dict[self.base_type] = {}
        mdict = self.to_dict(**kwargs)
        if self.mat is not None:
            if hasattr(self.mat, 'add_to_dict'):
                self.mat.add_to_dict(models_dict, **kwargs)
            else:
                if "material" not in models_dict:
                    models_dict["material"] = {}
                models_dict["material"][self.mat.unique_hash] = self.mat.to_dict(**kwargs)

            mdict['material_id'] = self.mat.id
            mdict['material_unique_hash'] = self.mat.unique_hash

        if return_mdict:
            return mdict
        models_dict[self.base_type][self.unique_hash] = mdict


class RCBeamSection(Section):
    id = None
    type = "rc_beam_section"
    base_type = "section"
    cracked_ratio = None
    _mom_cracked = None
    _mom_yield = None
    _mom_ult = None
    rc_mat = None

    def __init__(self, **kwargs):
        super(RCBeamSection, self).__init__(**kwargs)
        self._extra_class_inputs = ["cracked_ratio", "mom_cracked", "mom_yield", "mom_ult"]
        self.inputs = self.inputs + self._extra_class_inputs

    @property
    def i_rot_ww_cracked(self):
        try:
            return self.cracked_ratio * self.i_rot_ww
        except TypeError:
            return None

    @property
    def i_rot_dd_cracked(self):
        try:
            return self.cracked_ratio * self.i_rot_dd
        except TypeError:
            return None

    @property
    def mom_cracked(self):
        return self._mom_cracked

    @mom_cracked.setter
    def mom_cracked(self, value):
        self._mom_cracked = value

    @property
    def mom_yield(self):
        return self._mom_yield

    @mom_yield.setter
    def mom_yield(self, value):
        self._mom_yield = value

    @property
    def mom_ult(self):
        return self._mom_ult

    @mom_ult.setter
    def mom_ult(self, value):
        self._mom_ult = value

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

