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
