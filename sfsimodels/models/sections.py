import numpy as np
from sfsimodels.models.abstract_models import PhysicalObject


class Section(PhysicalObject):
    id = None
    type = "section"
    base_type = "section"
    _depth = None
    _width = None
    _material = None
    loading_pre_reqs = ('material',)

    def __init__(self, **kwargs):
        self.inputs = [
            "base_type",
            "type",
            "depth",
            "width",
            "material"
                       ]
        self.skip_list = list(self.skip_list) + ['material']

        for param in kwargs:
            if param in self.inputs:
                setattr(self, param, kwargs[param])

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
    def area(self):
        return self._width * self._depth

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


class RCDetailedSection(RCBeamSection):
    id = None
    type = "rc_beam_detailed_section"
    base_type = "section"

    def __init__(self, **kwargs):
        """
        A detailed section contains the position and size of the reinforcing elements
        Parameters
        ----------
        kwargs
        """
        super(RCDetailedSection, self).__init__(**kwargs)
        self._extra_class_inputs = ["layer_depths", "bar_diams", "bar_centres"]
        self.inputs = self.inputs + self._extra_class_inputs
        self.layer_depths = None
        self.bar_diams = None
        self.bar_centres = None
        self.db_trans = None
        self.spacing_trans = None  # centreline spacing
        self.fy_trans = None
        self.fy_long = None
        self.fu_long = None
        self.nb_trans_x = None
        self.nb_trans_y = None

    @property
    def cover_h(self):
        if self.layer_depths is not None:
            return min([self.layer_depths[0], self.depth - self.layer_depths[-1]])

    @property
    def cover_w(self):
        if self.bar_centres is not None:
            x_left = min([min(layer) for layer in self.bar_centres])
            x_right = min([min(layer) for layer in self.bar_centres])
            return min([x_left, self.width - x_right])

    @property
    def depth_c(self):
        """Depth of core section enclosed by the centre lines of transverse reinforcing"""
        if self.bar_diams is not None and self.db_trans is not None:
            db_av = (self.bar_diams[0][0] + self.bar_diams[-1][0]) / 2
            bar_tran_centre_d = self.cover_h - db_av / 2 + self.db_trans / 2
            return self.depth - 2 * bar_tran_centre_d

    @property
    def width_c(self):
        """Width of core section enclosed by the centre lines of transverse reinforcing"""
        if self.bar_diams is not None and self.db_trans is not None:
            db_av = (self.bar_diams[0][0] + self.bar_diams[-1][0]) / 2
            bar_tran_centre_w = self.cover_w - db_av / 2 + self.db_trans / 2
            return self.width - 2 * bar_tran_centre_w
        
    @property
    def area_c(self):
        """Area  of core section enclosed by the centre lines of transverse reinforcing"""
        if self.bar_diams is not None and self.db_trans is not None:
            return self.depth_c * self.width_c
        
    @property
    def area_steel(self):
        if self.bar_diams is not None:
            return np.sum(np.concatenate(self.bar_diams) ** 2 * np.pi / 4)

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

