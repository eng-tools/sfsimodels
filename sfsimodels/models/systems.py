from collections import OrderedDict
from sfsimodels.models import SoilProfile, Foundation, Building, Structure
from sfsimodels.exceptions import ModelError


class SoilStructureSystem(object):
    id = None
    name = None
    _sp = SoilProfile()
    _bd = Structure()
    _fd = Foundation()
    _soil_profile_id = None
    _building_id = None
    _foundation_id = None

    def __init__(self):
        self.inputs = ["id", "name", "soil_profile_id", "building_id", "foundation_id"]

    def to_dict(self):
        outputs = OrderedDict()
        skip_list = []
        for item in self.inputs:
            if item not in skip_list:
                value = self.__getattribute__(item)
                if "_id" in item and value is None:
                    raise ModelError("Cannot export system with %s set to None" % item)
                if isinstance(value, int):
                    outputs[item] = str(value)
                else:
                    outputs[item] = value
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
    def fd(self):
        return self._fd

    @fd.setter
    def fd(self, obj):
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
