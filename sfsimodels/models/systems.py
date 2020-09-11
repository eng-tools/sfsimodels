from collections import OrderedDict
from sfsimodels.models import SoilProfile, Foundation, SDOFBuilding
from sfsimodels.exceptions import ModelError
from sfsimodels import functions as sf
import uuid
import numpy as np


class SoilStructureSystem(object):
    id = None
    name = None
    base_type = "system"
    type = "sfs"
    _unique_hash = None
    _sp = SoilProfile()
    _bd = SDOFBuilding()
    _fd = Foundation()
    _soil_profile_id = None
    _building_id = None
    _foundation_id = None

    def __init__(self):
        self.inputs = ["id", "name", "soil_profile_id", "building_id", "foundation_id"]

    def to_dict(self, **kwargs):
        outputs = OrderedDict()
        skip_list = []
        for item in self.inputs:
            if item not in skip_list:
                value = self.__getattribute__(item)
                if "_id" in item and value is None:
                    raise ModelError("Cannot export system with %s set to None" % item)
                if item not in skip_list:
                    value = self.__getattribute__(item)
                    outputs[item] = sf.collect_serial_value(value)
        return outputs

    def add_obj_to_system(self, obj):
        if hasattr(obj, "base_type"):
            if obj.base_type == "soil":
                self.sp = obj
                self._soil_profile_id = obj.id

            elif obj.base_type == "foundation":
                self.fd = obj
                self._foundation_id = obj.id
            elif obj.base_type == "building":
                self.bd = obj
                self._building_id = obj.id

    @property
    def soil_profile_id(self):
        if self._soil_profile_id is None:
            if self._sp.id is not None:
                self._soil_profile_id = self._sp.id
        return self._soil_profile_id

    @property
    def foundation_id(self):
        if self._foundation_id is None:
            if self._fd.id is not None:
                self._foundation_id = self._fd.id
        return self._foundation_id

    @property
    def building_id(self):
        if self._building_id is None:
            if self._bd.id is not None:
                self._building_id = self._bd.id
        return self._building_id

    @property
    def sp(self):
        return self._sp

    @sp.setter
    def sp(self, obj):
        # Could add assertions here for type?
        self._sp = obj
        self._soil_profile_id = obj.id

    @property
    def soil_profile(self):
        return self._sp

    @soil_profile.setter
    def soil_profile(self, obj):
        # Could add assertions here for type?
        self._sp = obj
        self._soil_profile_id = obj.id

    @property
    def fd(self):
        return self._fd

    @fd.setter
    def fd(self, obj):
        # Could add assertions here for type?
        self._fd = obj
        self._foundation_id = obj.id

    @property
    def foundation(self):
        return self._fd

    @foundation.setter
    def foundation(self, obj):
        # Could add assertions here for type?
        self._fd = obj
        self._foundation_id = obj.id

    @property
    def bd(self):
        return self._bd

    @bd.setter
    def bd(self, obj):
        # Could add assertions here for type?
        self._bd = obj
        self._building_id = obj.id

    @property
    def building(self):
        return self._bd

    @building.setter
    def building(self, obj):
        # Could add assertions here for type?
        self._bd = obj
        self._building_id = obj.id

    @property
    def unique_hash(self):
        if self._unique_hash is None:
            self._unique_hash = uuid.uuid1()
        return self._unique_hash


class TwoDSystem(object):
    _unique_hash = None
    base_type = 'system'
    type = 'two_d_system'
    name = None

    def __init__(self, width, height, x_surf=None, y_surf=None):
        self.width = width
        self.height = height
        if x_surf is None:
            self.x_surf = np.array([0, width])
            self.y_surf = np.array([0, 0])
        else:
            self.x_surf = np.array(x_surf)
            self.y_surf = np.array(y_surf)

        self._sps = []
        self._x_sps = []

        self._bds = []
        self._x_bds = []
        self.inputs = ["id", "name", "width", "height", "sps", "x_sps", "bds", "x_bds", "x_surf", "y_surf"]
        self.gwl = 1e6  # can be coordinates

    def to_dict(self, **kwargs):
        outputs = OrderedDict()
        skip_list = ['sps', 'bds']
        for item in self.inputs:
            if item not in skip_list:
                value = self.__getattribute__(item)
                if "_id" in item and value is None:
                    raise ModelError("Cannot export system with %s set to None" % item)
                if item not in skip_list:
                    value = self.__getattribute__(item)
                    outputs[item] = sf.collect_serial_value(value)
        return outputs

    def add_to_dict(self, models_dict, **kwargs):
        if self.base_type not in models_dict:
            models_dict[self.base_type] = OrderedDict()
        if "soil_profile" not in models_dict:
            models_dict["soil_profile"] = OrderedDict()
        if "building" not in models_dict:
            models_dict["building"] = OrderedDict()
        if "foundation" not in models_dict:
            models_dict["foundation"] = OrderedDict()
        profile_dict = self.to_dict(**kwargs)
        profile_dict["sps"] = []
        for i, sp in enumerate(self.sps):
            sp.add_to_dict(models_dict, **kwargs)
            if sp.id is None:
                sp.id = i + 1
            sp.set_soil_ids_to_layers()
            profile_dict["sps"].append({
                "soil_profile_id": str(sp.id),
                "soil_profile_unique_hash": str(sp.unique_hash),
            })
        profile_dict["bds"] = []
        for i, bd in enumerate(self.bds):
            if bd.id is None:
                bd.id = i + 1
            if bd.fd is not None:
                if bd.fd.id is None:
                    bd.fd.id = i + 1
                if hasattr(bd.fd, "add_to_dict"):
                    bd.fd.add_to_dict(models_dict, **kwargs)
                else:
                    models_dict["foundation"][bd.fd.unique_hash] = bd.fd.to_dict(**kwargs)
            if hasattr(bd, "add_to_dict"):
                bd.add_to_dict(models_dict, **kwargs)
            else:
                models_dict["building"][bd.unique_hash] = bd.to_dict(**kwargs)
            profile_dict["bds"].append({
                "building_id": str(bd.id),
                "building_hash": str(bd.unique_hash),
            })


        models_dict[self.base_type][self.unique_hash] = profile_dict

    def add_sp(self, sp, x):
        self._x_sps.append(x)
        self._sps.append(sp)

    @property
    def sps(self):
        return self._sps

    @property
    def x_sps(self):
        return self._x_sps

    @property
    def bds(self):
        return self._bds

    def add_bd(self, bd, x):
        self._x_bds.append(x)
        self._bds.append(bd)

    @property
    def x_bds(self):
        return self._x_bds

    @property
    def unique_hash(self):
        if self._unique_hash is None:
            self._unique_hash = uuid.uuid1()
        return self._unique_hash

    def get_y_surface_at_x(self, x):
        return np.interp(x, self.x_surf, self.y_surf)
