

class SoilStructureSystem(object):
    name = None
    soil_profile_id = None
    building_id = None
    foundation_id = None

    def to_dict(self):
        return self.__dict__
