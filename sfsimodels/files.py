import json
from sfsimodels.models import soils, buildings, foundations, material, systems, abstract_models
from collections import OrderedDict
from sfsimodels import models
from sfsimodels.exceptions import deprecation, ModelError


def add_to_obj(obj, dictionary, exceptions=[], verbose=0):
    """
    Cycles through a dictionary and adds the key-value pairs to an object.

    :param obj:
    :param dictionary:
    :param exceptions:
    :param verbose:
    :return:
    """
    for item in dictionary:
        if item in exceptions:
            continue
        if dictionary[item] is not None:
            if verbose:
                print("assign: ", item, dictionary[item])
            setattr(obj, item, dictionary[item])


def load_json(ffp, custom=None, meta=False, verbose=0):
    """
    Given a json file it creates a dictionary of sfsi objects

    :param ffp: str, Full file path to json file
    :param custom: dict, used to load custom objects, {model type: custom object}
    :param verbose: int, console output
    :return: dict
    """
    data = json.load(open(ffp))
    if meta:
        md = {}
        for item in data:
            if item != "models":
                md[item] = data[item]
        return ecp_dict_to_objects(data, custom, verbose=verbose), md
    else:
        return ecp_dict_to_objects(data, custom, verbose=verbose)


def loads_json(p_str, custom=None, meta=False, verbose=0):
    """
    Given a json string it creates a dictionary of sfsi objects

    :param ffp: str, Full file path to json file
    :param custom: dict, used to load custom objects, {model type: custom object}
    :param meta: bool, if true then also return all ecp meta data in separate dict
    :param verbose: int, console output
    :return: dict
    """
    data = json.loads(p_str)
    if meta:
        md = {}
        for item in data:
            if item != "models":
                md[item] = data[item]
        return ecp_dict_to_objects(data, custom, verbose=verbose), md
    else:
        return ecp_dict_to_objects(data, custom, verbose=verbose)


# Deprecated name
def dicts_to_objects(data, verbose=0):
    """Deprecated. Use ecp_dict_to_objects"""
    deprecation('Deprecated, dicts_to_objects should be switched to ecp_dict_to_objects')
    ecp_dict_to_objects(data, verbose=verbose)


def ecp_dict_to_objects(ecp_dict, custom_map=None, verbose=0):
    """
    Given an ecp dictionary, build a dictionary of sfsi objects

    :param ecp_dict: dict, engineering consistency project dictionary
    :param custom: dict, used to load custom objects, {model type: custom object}
    :param verbose: int, console output
    :return: dict
    """
    if custom_map is None:
        custom_map = {}

    obj_map = {
        "soil-soil": soils.Soil,
        "soil-critical_soil": soils.Soil,
        "soil_profile-soil_profile": soils.SoilProfile,
        "building-building": buildings.Building,
        "building-frame_building": buildings.FrameBuilding,
        "building-frame_building_2D": buildings.FrameBuilding2D,
        "building-wall_building": buildings.WallBuilding,
        "building-structure": buildings.Structure,
        "foundation-foundation": foundations.Foundation,
        "foundation-raft_foundation": foundations.RaftFoundation,
        "foundation-raft": foundations.RaftFoundation,  # Deprecated approach for type
        "foundation-pad_foundation": foundations.PadFoundation,
        "section-section": buildings.Section,
        "custom_object-custom_object": abstract_models.CustomObject
    }
    # merge and overwrite the object map with custom maps
    for item in custom_map:
        obj_map[item] = custom_map[item]

    data_models = ecp_dict["models"]

    exception_list = ["soil_profiles", "buildings", "systems"]
    objs = OrderedDict()
    for mtype in data_models:
        base_type = mtype[:-1]  # remove the 's'
        objs[mtype] = OrderedDict()
        if mtype in exception_list:
            continue
        for m_id in data_models[mtype]:
            obj = data_models[mtype][m_id]
            if "type" not in obj:
                obj["type"] = base_type
            try:
                obj_class = obj_map["%s-%s" % (base_type, obj["type"])]
            except KeyError:
                raise KeyError("Map for Model: '%s' index: '%s' and type: '%s' not available, "
                               "add '%s-%s' to custom dict" % (mtype, m_id, base_type, base_type, obj["type"]))
            new_instance = obj_class()
            add_to_obj(new_instance, data_models[mtype][m_id], verbose=verbose)
            # print(mtype, m_id)
            objs[mtype][int(data_models[mtype][m_id]["id"])] = new_instance

    if "soil_profiles" in data_models:
        for m_id in data_models["soil_profiles"]:
            new_soil_profile = soils.SoilProfile()
            new_soil_profile.id = data_models["soil_profiles"][m_id]["id"]
            for j in range(len(data_models["soil_profiles"][m_id]["layers"])):
                depth = data_models["soil_profiles"][m_id]['layers'][j]["depth"]
                soil = objs["soils"][int(data_models["soil_profiles"][m_id]['layers'][j]["soil_id"])]
                new_soil_profile.add_layer(depth, soil)
            add_to_obj(new_soil_profile, data_models["soil_profiles"][m_id], exceptions=["layers"], verbose=verbose)
            objs["soil_profiles"][int(data_models["soil_profiles"][m_id]["id"])] = new_soil_profile

    # if "foundations" in data_models:
    #     for m_id in data_models["foundations"]:
    #         if data_models["foundations"][m_id]["type"] == "raft":
    #             new_foundation = foundations.RaftFoundation()
    #         elif data_models["foundations"][m_id]["type"] == "pad":
    #             new_foundation = foundations.PadFoundation()
    #         else:
    #             new_foundation = foundations.Foundation()
    #         new_foundation.id = data_models["foundations"][m_id]["id"]
    #         add_to_obj(new_foundation, data_models["foundations"][m_id], verbose=verbose)
    #         foundation_objs[int(data_models["foundations"][m_id]["id"])] = new_foundation
    #
    # if "sections" in data_models:
    #     for m_id in data_models["section"]:
    #         new_section = buildings.Section()
    #         add_to_obj(new_section, data_models["section"][m_id], verbose=verbose)
    #         section_objs[int(data_models["section"][m_id]["id"])] = new_section

    if "buildings" in data_models:
        for m_id in data_models["buildings"]:
            obj = data_models["buildings"][m_id]
            if obj["type"] in ["structure"]:
                new_building = obj_map["%s-%s" % ("building", obj["type"])]()
            elif "frame_building" in obj["type"]:
                n_storeys = len(obj['interstorey_heights'])
                n_bays = len(obj['bay_lengths'])
                new_building = obj_map["%s-%s" % ("building", obj["type"])](n_storeys, n_bays)
                for ss in range(n_storeys):
                    for bb in range(n_bays):
                        beam_sect_id = str(obj["beam_section_ids"][ss][bb])
                        sect_dictionary = obj["beam_sections"][beam_sect_id]
                        add_to_obj(new_building.beams[ss][bb], sect_dictionary, verbose=verbose)
                    for cc in range(n_bays + 1):
                        column_sect_id = str(obj["column_section_ids"][ss][cc])
                        sect_dictionary = obj["column_sections"][column_sect_id]
                        add_to_obj(new_building.columns[ss][cc], sect_dictionary, verbose=verbose)

            else:
                n_storeys = len(obj['interstorey_heights'])
                new_building = obj_map["%s-%s" % ("building", obj["type"])](n_storeys)
            add_to_obj(new_building, data_models["buildings"][m_id], verbose=verbose)
            objs["buildings"][int(data_models["buildings"][m_id]["id"])] = new_building

    if "systems" in data_models:  # must be run after other objects are loaded
        for m_id in data_models["systems"]:
            new_system = systems.SoilStructureSystem()

            # Attach the soil profile
            soil_profile_id = data_models["systems"][m_id]['soil_profile_id']
            soil_profile = objs["soil_profiles"][int(soil_profile_id)]
            new_system.sp = soil_profile

            # Attach the foundation
            foundation_id = data_models["systems"][m_id]['foundation_id']
            foundation = objs["foundations"][int(foundation_id)]
            new_system.fd = foundation

            # Attach the building
            building_id = data_models["systems"][m_id]['building_id']
            building = objs["buildings"][int(building_id)]
            new_system.bd = building

            # Add remaining parameters
            ignore_list = ["foundation_id", "building_id", "soil_profile_id"]
            add_to_obj(new_system, data_models["systems"][m_id], exceptions=ignore_list, verbose=verbose)
            objs["systems"][int(data_models["systems"][m_id]["id"])] = new_system

    # # Catch custom types
    # standard_types = ["soils", "soil_profiles", "foundations", "sections", "buildings", "systems"]
    # for m_type in data_models:
    #     if m_type not in standard_types and m_type in custom:
    #         if m_type not in all_custom_objs:
    #             all_custom_objs[m_type] = {}
    #         for m_id in data_models[m_type]:
    #             if "id" not in data_models[m_type][m_id]:
    #                 raise ModelError("object (%s) requires 'id' parameter" % m_type)
    #             new_custom_obj = custom[m_type]()  # Note currently no support for custom objects
    #             add_to_obj(new_custom_obj, data_models[m_type][m_id], verbose=verbose)
    #             all_custom_objs[m_type][int(data_models[m_type][m_id]["id"])] = new_custom_obj
    #
    #
    # for m_type in all_custom_objs:
    #     objs[m_type] = all_custom_objs[m_type]
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

    def add_to_dict(self, an_object, extras={}):
        """
        Convert models to json serialisable output

        :param an_object: An instance of a model object
        :param extras: A dictionary of extra variables that should be
        :return:
        """
        if an_object.id is None:
            raise ModelError("id must be set on object before adding to output.")
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
        elif isinstance(an_object, models.Foundation):  # This is redundant, custom catcher at end works for all
            self.models["foundations"][an_object.id] = an_object.to_dict()
        elif isinstance(an_object, models.Structure):
            self.models["buildings"][an_object.id] = an_object.to_dict()
        elif isinstance(an_object, models.Building):
            self.models["buildings"][an_object.id] = an_object.to_dict()
        elif isinstance(an_object, models.SoilStructureSystem):
            self.models["systems"][an_object.id] = an_object.to_dict()
        elif hasattr(an_object, "to_dict"):  # Catch any custom objects
            if hasattr(an_object, "type"):
                mtype = an_object.type + "s"
                if mtype not in self.models:
                    self.models[mtype] = OrderedDict()
                self.models[mtype][an_object.id] = an_object.to_dict()
            else:
                raise ModelError("Object does not have attribute 'type', cannot add to output.")
        else:
            raise ModelError("Object does not have method 'to_dict', cannot add to output.")

    def add_to_output(self, mtype, m_id, serialisable_dict):
        """
        Can add additional objects or dictionaries to output file that don't conform to standard objects.

        :param mtype:
        :param m_id:
        :param serialisable_dict:
        :return:
        """
        if mtype not in self.models:
            self.models[mtype] = OrderedDict()
        self.models[mtype][m_id] = serialisable_dict


    @staticmethod
    def parameters():
        return ["name", "units", "doi", "sfsimodels_version", "comments", "models"]

    def to_dict(self):
        outputs = OrderedDict()
        for item in self.parameters():
            outputs[item] = self.__getattribute__(item)
        return outputs
