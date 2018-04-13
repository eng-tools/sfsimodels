import json
from sfsimodels.models import soils, buildings, foundations, material, systems
from collections import OrderedDict
from sfsimodels import models


def add_to_obj(obj, dictionary, exceptions=[], verbose=False):
    """
    Cycles through a dictionary and adds the key-value pairs to an object.

    :param obj:
    :param dictionary:
    :param exceptions:
    :param verbose:
    :return:
    """
    for item in obj.inputs:
        if item in exceptions:
            continue
        if item in dictionary and dictionary[item] is not None and hasattr(obj, item):
            if verbose:
                print("assign: ", item, dictionary[item])
            setattr(obj, item, dictionary[item])


def load_yaml(fp):
    import yaml  # Not in dependencies

    data = yaml.load(open(fp))
    soil_objs = {}
    soil_profile_objs = {}
    foundation_objs = {}
    if "Soils" in data:
        for i in range(len(data["Soils"])):
            new_soil = soils.Soil()
            add_to_obj(new_soil, data["Soils"][i])
            soil_objs[data["Soils"][i]["_id"]] = new_soil

    if "SoilProfiles" in data:
        for i in range(len(data["SoilProfiles"])):
            new_soil_profile = soils.SoilProfile()
            new_soil_profile.id = data["SoilProfiles"][i]["_id"]
            for j in range(len(data["SoilProfiles"][i]["layers"])):
                depth = data["SoilProfiles"][i]['layers'][j]["depth"]
                soil = soil_objs[data["SoilProfiles"][i]['layers'][j]["soil_id"]]
                new_soil_profile.add_layer(depth, soil)
            add_to_obj(new_soil_profile, data["SoilProfiles"][i], exceptions=["layers"])
            soil_profile_objs[data["SoilProfiles"][i]["_id"]] = new_soil_profile

    if "Foundations" in data:
        for i in range(len(data["Foundations"])):
            if data["Foundations"][i]["type"] == "raft":
                new_foundation = foundations.RaftFoundation()
            elif data["Foundations"][i]["type"] == "pad":
                new_foundation = foundations.PadFoundation()
            else:
                new_foundation = foundations.Foundation()
            new_foundation.id = data["Foundations"][i]["_id"]
            add_to_obj(new_foundation, data["Foundations"][i])
            foundation_objs[data["Foundations"][i]["_id"]] = new_foundation

    objs = {
        "soils": soil_objs,
        "soil_profiles": soil_profile_objs,
        "foundations": foundation_objs

    }

    return objs


def load_json(fp):
    data = json.load(open(fp))
    return dicts_to_objects(data)


def loads_json(p_str, verbose=0):
    data = json.loads(p_str)
    return dicts_to_objects(data, verbose=verbose)


def dicts_to_objects(data, verbose=0):

    models = data["models"]
    soil_objs = {}
    soil_profile_objs = {}
    foundation_objs = {}
    building_objs = {}
    system_objs = {}
    if "soils" in models:
        for id in models["soils"]:
            new_soil = soils.Soil()
            add_to_obj(new_soil, models["soils"][id], verbose=verbose)
            soil_objs[int(models["soils"][id]["id"])] = new_soil

    if "soil_profiles" in models:
        for id in models["soil_profiles"]:
            new_soil_profile = soils.SoilProfile()
            new_soil_profile.id = models["soil_profiles"][id]["id"]
            for j in range(len(models["soil_profiles"][id]["layers"])):
                depth = models["soil_profiles"][id]['layers'][j]["depth"]
                soil = soil_objs[int(models["soil_profiles"][id]['layers'][j]["soil_id"])]
                new_soil_profile.add_layer(depth, soil)
            add_to_obj(new_soil_profile, models["soil_profiles"][id], exceptions=["layers"], verbose=verbose)
            # for item in new_soil_profile.inputs:
            #     if item == "layers":
            #         continue  # layers already loaded
            #     if item in models["SoilProfiles"][i] and hasattr(new_soil_profile, item):
            #         setattr(new_soil_profile, item, models["SoilProfiles"][i][item])
            #         print("assign: ", item, models["SoilProfiles"][i][item])
            soil_profile_objs[int(models["soil_profiles"][id]["id"])] = new_soil_profile

    if "foundations" in models:
        for id in models["foundations"]:
            if models["foundations"][id]["type"] == "raft":
                new_foundation = foundations.RaftFoundation()
            elif models["foundations"][id]["type"] == "pad":
                new_foundation = foundations.PadFoundation()
            else:
                new_foundation = foundations.Foundation()
            new_foundation.id = models["foundations"][id]["id"]
            add_to_obj(new_foundation, models["foundations"][id], verbose=verbose)
            foundation_objs[int(models["foundations"][id]["id"])] = new_foundation

    if "buildings" in models:
        for id in models["buildings"]:
            if models["buildings"][id]["type"] == "structure":
                new_building = buildings.Structure()
            elif models["buildings"][id]["type"] == "building":
                new_building = buildings.Building()
            else:
                new_building = buildings.Building()
            add_to_obj(new_building, models["buildings"][id], verbose=verbose)
            building_objs[int(models["buildings"][id]["id"])] = new_building
    if "systems" in models:
        for id in models["systems"]:
            new_system = systems.SoilStructureSystem()
            add_to_obj(new_system, models["systems"][id], verbose=verbose)
            system_objs[int(models["systems"][id]["id"])] = new_system

    objs = {
        "soils": soil_objs,
        "soil_profiles": soil_profile_objs,
        "foundations": foundation_objs,
        "buildings": building_objs,
        "systems": system_objs,

    }

    return objs


class Output(object):
    name = ""
    units = ""
    doi = ""
    sfsimodels_version = ""
    comments = ""

    def __init__(self):
        self.models = OrderedDict([("soils", OrderedDict()),
                            ("soil_profiles", OrderedDict()),
                            ("foundations", OrderedDict()),
                            ("buildings", OrderedDict()),
                            ("systems", OrderedDict()),
                            ])

    def add_to_dict(self, an_object):
        if isinstance(an_object, models.Soil):
            self.models["soils"][an_object.id] = an_object.to_dict()
        elif isinstance(an_object, models.SoilProfile):
            profile_dict = an_object.to_dict()
            profile_dict["layers"] = []
            for layer in an_object.layers:
                self.models["soils"][an_object.layers[layer].id] = an_object.layers[layer].to_dict()
                profile_dict["layers"].append({
                    "soil_id": str(an_object.layers[layer].id),
                    "depth": float(layer)
                })

            self.models["soil_profiles"][an_object.id] = profile_dict
        elif isinstance(an_object, models.Foundation):
            self.models["foundations"][an_object.id] = an_object.to_dict()
        elif isinstance(an_object, models.Structure):
            self.models["buildings"][an_object.id] = an_object.to_dict()
        elif isinstance(an_object, models.Building):
            self.models["buildings"][an_object.id] = an_object.to_dict()
        elif isinstance(an_object, models.SoilStructureSystem):
            self.models["systems"][an_object.id] = an_object.to_dict()

    @staticmethod
    def parameters():
        return ["name", "units", "doi", "sfsimodels_version", "comments", "models"]

    def to_dict(self):
        outputs = OrderedDict()
        for item in self.parameters():
            outputs[item] = self.__getattribute__(item)
        return outputs



if __name__ == '__main__':
    fp = "../tests/test_data/_object_load_1.yaml"
    load_yaml(fp)
