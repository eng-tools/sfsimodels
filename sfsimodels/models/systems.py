from collections import OrderedDict


class SoilStructureSystem(object):
    id = None
    name = None
    soil_profile_id = None
    building_id = None
    foundation_id = None

    inputs = ["soil_profile_id", "building_id", "foundation_id"]

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
