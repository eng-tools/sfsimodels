import yaml
from sfsimodels.models import soils, buildings, foundations, material


def add_to_obj(obj, dictionary, exceptions=[]):
    for item in obj.inputs:
        if item in exceptions:
            continue
        if item in dictionary and hasattr(obj, item):
            setattr(obj, item, dictionary[item])
            print("assign: ", item, dictionary[item])

def load_yaml(fp):

    data = yaml.load(open(fp))
    soil_objs = {}
    soil_profile_objs = {}
    foundation_objs = {}
    if "Soils" in data:
        for i in range(len(data["Soils"])):
            new_soil = soils.Soil()
            for item in new_soil.inputs:
                if item in data["Soils"][i] and hasattr(new_soil, item):
                    setattr(new_soil, item, data["Soils"][i][item])
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
            # for item in new_soil_profile.inputs:
            #     if item == "layers":
            #         continue  # layers already loaded
            #     if item in data["SoilProfiles"][i] and hasattr(new_soil_profile, item):
            #         setattr(new_soil_profile, item, data["SoilProfiles"][i][item])
            #         print("assign: ", item, data["SoilProfiles"][i][item])
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

    print(data)
    print(foundation_objs[0])
    objs = {
        "soils": soil_objs,
        "soil_profiles": soil_profile_objs,
        "foundations": foundation_objs

    }

    return objs


if __name__ == '__main__':
    fp = "../tests/test_data/_object_load_1.yaml"
    load_yaml(fp)
