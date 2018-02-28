from collections import OrderedDict

from sfsimodels import models


class System(object):
    obj_dict = OrderedDict([("soils", []),
                            ("soil_profiles", []),
                            ("foundations", []),
                            ("buildings", []),
                            ])

    def add_to_dict(self, an_object):
        if isinstance(an_object, models.Soil):
            self.obj_dict["soils"] = an_object.to_dict()
        elif isinstance(an_object, models.SoilProfile):
            self.obj_dict["soil_profiles"] = an_object.to_dict()
        elif isinstance(an_object, models.Foundation):
            self.obj_dict["foundations"] = an_object.to_dict()
        elif isinstance(an_object, models.Structure):
            self.obj_dict["buildings"] = an_object.to_dict()
        elif isinstance(an_object, models.Building):
            self.obj_dict["buildings"] = an_object.to_dict()

    def to_dict(self):
        return self.obj_dict
