from collections import OrderedDict
from sfsimodels.models import SoilProfile, Foundation, Building, Structure


class SoilStructureSystem(object):
    id = None
    name = None
    sp = SoilProfile()
    bd = Structure()
    fd = Foundation()
    soil_profile_id = None
    building_id = None
    foundation_id = None

    inputs = ["id", "name", "soil_profile_id", "building_id", "foundation_id"]

    def to_dict(self):
        outputs = OrderedDict()
        skip_list = []
        for item in self.inputs:
            if item not in skip_list:
                value = self.__getattribute__(item)
                if isinstance(value, int):
                    outputs[item] = str(value)
                else:
                    outputs[item] = value
        return outputs

    def add_obj_to_system(self, obj):
        if isinstance(obj, SoilProfile):
            self.sp = obj
            self.soil_profile_id = obj.id  # TODO: make id methods protected with only getter methods

        elif isinstance(obj, Foundation):
            self.fd = obj
            self.foundation_id = obj.id
        elif isinstance(obj, Structure):
            self.bd = obj
            self.building_id = obj.id
