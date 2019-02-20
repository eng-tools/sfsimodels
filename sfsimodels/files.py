import json
from sfsimodels.models import soils, buildings, foundations, material, systems, abstract_models
from collections import OrderedDict
from sfsimodels import models
from sfsimodels.exceptions import deprecation, ModelError


standard_types = ["soil", "soil_profile", "foundation", "building", "section", "system", "custom_type"]


def add_to_obj(obj, dictionary, exceptions=None, verbose=0):
    """
    Cycles through a dictionary and adds the key-value pairs to an object.

    :param obj:
    :param dictionary:
    :param exceptions:
    :param verbose:
    :return:
    """
    if exceptions is None:
        exceptions = []
    for item in dictionary:
        if item in exceptions:
            continue
        if dictionary[item] is not None:
            if verbose:
                print("assign: ", item, dictionary[item])
            setattr(obj, item, dictionary[item])


def load_json(ffp, custom=None, verbose=0):
    """
    Given a json file it creates a dictionary of sfsi objects

    :param ffp: str, Full file path to json file
    :param custom: dict, used to load custom objects, {model type: custom object}
    :param verbose: int, console output
    :return: dict
    """
    data = json.load(open(ffp))
    return ecp_dict_to_objects(data, custom, verbose=verbose)


def load_json_and_meta(ffp, custom=None, verbose=0):
    data = json.load(open(ffp))
    md = {}
    for item in data:
        if item != "models":
            md[item] = data[item]
    return ecp_dict_to_objects(data, custom, verbose=verbose), md


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


deprecated_types = OrderedDict([
    ("structure", "sdof"),
    ("frame_building", "building_frame"),
    ("frame_building_2D", "building_frame2D"),
    ("wall_building", "building_wall"),
    ("pad_foundation", "foundation_pad"),
    ("raft_foundation", "foundation_raft")
])


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
        "soil-critical_soil": soils.CriticalSoil,
        "soil-soil_critical": soils.CriticalSoil,  # deprecated type
        "soil-stress_dependent_soil": soils.StressDependentSoil,
        "soil-soil_stress_dependent": soils.StressDependentSoil,
        "soil_profile-soil_profile": soils.SoilProfile,
        "building-building": buildings.Building,
        "building-frame_building": buildings.FrameBuilding,
        "building-frame_building2D": buildings.FrameBuilding2D,
        "building-building_frame2D": buildings.FrameBuilding2D,  # deprecated type
        "building-wall_building": buildings.WallBuilding,
        "building-building_wall": buildings.WallBuilding,  # deprecated type
        "building-structure": buildings.SDOFBuilding,  # Deprecated type, remove in v1
        "building-sdof": buildings.SDOFBuilding,
        "foundation-foundation": foundations.Foundation,
        "foundation-foundation_raft": foundations.RaftFoundation,  # deprecated type
        "foundation-raft_foundation": foundations.RaftFoundation,
        "foundation-raft": foundations.RaftFoundation,  # Deprecated approach for type, remove in v1
        "foundation-pad_foundation": foundations.PadFoundation,
        "foundation-foundation_pad": foundations.PadFoundation,  # deprecated type
        "section-section": buildings.Section,
        "custom_object-custom_object": abstract_models.CustomObject,
        "system-system": systems.SoilStructureSystem,  # deprecated type
        "system-sfs": systems.SoilStructureSystem
    }

    # merge and overwrite the object map with custom maps
    for item in custom_map:
        obj_map[item] = custom_map[item]

    data_models = ecp_dict["models"]

    exception_list = ["soil_profile", "building", "system"]
    objs = OrderedDict()
    collected = set([])
    # Set base type properly
    mtypes = list(data_models)
    for mtype in mtypes:
        base_type = mtype
        if base_type[:-1] in standard_types:  # support the loading of old plural based ecp files
            base_type = base_type[:-1]
            data_models[base_type] = data_models[mtype]
            del data_models[mtype]
        for m_id in data_models[base_type]:
            data_models[base_type][m_id]["base_type"] = base_type

    for mtype in data_models:
        base_type = mtype
        if base_type in exception_list:
            continue
        collected.add(base_type)
        objs[base_type] = OrderedDict()
        for m_id in data_models[mtype]:
            obj = data_models[mtype][m_id]
            if "type" not in obj:
                obj["type"] = base_type
            try:
                obj_class = obj_map["%s-%s" % (base_type, obj["type"])]
            except KeyError:
                if obj["type"] in deprecated_types:
                    try:
                        obj_class = obj_map["%s-%s" % (base_type, deprecated_types[obj["type"]])]
                    except KeyError:
                        raise KeyError("Map for Model: '%s' index: '%s' and type: '%s' not available, "
                                       "add '%s-%s' to custom dict" % (base_type, m_id, base_type, base_type, obj["type"]))
                else:
                    raise KeyError("Map for Model: '%s' index: '%s' and type: '%s' not available, "
                                   "add '%s-%s' to custom dict" % (base_type, m_id, base_type, base_type, obj["type"]))
            new_instance = obj_class()
            add_to_obj(new_instance, data_models[mtype][m_id], verbose=verbose)
            # print(mtype, m_id)
            objs[base_type][int(data_models[mtype][m_id]["id"])] = new_instance

    # Deal with all the exceptions
    for mtype in data_models:
        base_type = mtype

        if base_type in collected:
            continue
        if base_type not in objs:
            objs[base_type] = OrderedDict()

        if base_type == "soil_profile":
            if "soil" not in objs:
                objs["soil"] = OrderedDict()
            for m_id in data_models[mtype]:
                obj = data_models[mtype][m_id]
                if "type" not in obj:
                    obj["type"] = base_type
                try:
                    obj_class = obj_map["%s-%s" % (base_type, obj["type"])]
                except KeyError:
                    raise KeyError("Map for Model: '%s' index: '%s' and type: '%s' not available, "
                                   "add '%s-%s' to custom dict" % (mtype, m_id, base_type, base_type, obj["type"]))
                new_soil_profile = obj_class()
                new_soil_profile.id = data_models[mtype][m_id]["id"]
                for j in range(len(data_models[mtype][m_id]["layers"])):
                    depth = data_models[mtype][m_id]['layers'][j]["depth"]
                    soil = objs["soil"][int(data_models[mtype][m_id]['layers'][j]["soil_id"])]
                    new_soil_profile.add_layer(depth, soil)
                add_to_obj(new_soil_profile, data_models[mtype][m_id], exceptions=["layers"], verbose=verbose)
                objs[base_type][int(data_models[mtype][m_id]["id"])] = new_soil_profile

        if base_type == "building":
            for m_id in data_models[mtype]:
                obj = data_models[mtype][m_id]
                if obj["type"] in deprecated_types:
                    obj["type"] = deprecated_types[obj["type"]]
                if "type" not in obj:
                    obj["type"] = base_type
                if obj["type"] in ["sdof"]:
                    new_building = obj_map["%s-%s" % (base_type, obj["type"])]()
                elif "building_frame" in obj["type"] or "frame_building" in obj["type"]:
                    n_storeys = len(obj['interstorey_heights'])
                    n_bays = len(obj['bay_lengths'])
                    new_building = obj_map["%s-%s" % (base_type, obj["type"])](n_storeys, n_bays)
                    for ss in range(n_storeys):
                        for bb in range(n_bays):
                            sect_is = obj["beam_section_ids"][ss][bb]
                            if hasattr(sect_is, "__len__"):
                                n_sections = len(sect_is)
                                new_building.beams[ss][bb].split_into_multiple([1] * n_sections)  # TODO: should be lengths
                                for sect_i in range(len(sect_is)):
                                    beam_sect_id = str(obj["beam_section_ids"][ss][bb][sect_i])
                                    sect_dictionary = obj["beam_sections"][beam_sect_id]
                                    add_to_obj(new_building.beams[ss][bb].sections[sect_i], sect_dictionary, verbose=verbose)
                            else:  # deprecated loading
                                beam_sect_id = str(obj["beam_section_ids"][ss][bb])
                                sect_dictionary = obj["beam_sections"][beam_sect_id]
                                add_to_obj(new_building.beams[ss][bb].section[0], sect_dictionary, verbose=verbose)
                        for cc in range(n_bays + 1):
                            sect_is = obj["column_section_ids"][ss][cc]
                            if hasattr(sect_is, "__len__"):
                                n_sections = len(sect_is)
                                # TODO: should be lengths
                                new_building.columns[ss][cc].split_into_multiple([1] * n_sections)
                                for sect_i in range(len(sect_is)):
                                    column_sect_id = str(obj["column_section_ids"][ss][cc][sect_i])
                                    sect_dictionary = obj["column_sections"][column_sect_id]
                                    add_to_obj(new_building.columns[ss][cc].sections[sect_i], sect_dictionary, verbose=verbose)
                            else:
                                column_sect_id = str(obj["column_section_ids"][ss][cc])
                                sect_dictionary = obj["column_sections"][column_sect_id]
                                add_to_obj(new_building.columns[ss][cc].sections[0], sect_dictionary, verbose=verbose)

                else:
                    n_storeys = len(obj['interstorey_heights'])
                    new_building = obj_map["%s-%s" % (base_type, obj["type"])](n_storeys)
                add_to_obj(new_building, data_models[mtype][m_id], verbose=verbose)
                objs[base_type][int(data_models[mtype][m_id]["id"])] = new_building

        if base_type == "system":  # must be run after other objects are loaded
            for m_id in data_models[mtype]:
                obj = data_models[mtype][m_id]
                if "type" not in obj:
                    obj["type"] = base_type
                try:
                    obj_class = obj_map["%s-%s" % (base_type, obj["type"])]
                except KeyError:
                    raise KeyError("Map for Model: '%s' index: '%s' and type: '%s' not available, "
                                   "add '%s-%s' to custom dict" % (mtype, m_id, base_type, base_type, obj["type"]))
                new_system = obj_class()

                # Attach the soil profile
                soil_profile_id = data_models[mtype][m_id]['soil_profile_id']
                soil_profile = objs["soil_profile"][int(soil_profile_id)]
                new_system.sp = soil_profile

                # Attach the foundation
                foundation_id = data_models[mtype][m_id]['foundation_id']
                foundation = objs["foundation"][int(foundation_id)]
                new_system.fd = foundation

                # Attach the building
                building_id = data_models[mtype][m_id]['building_id']
                building = objs["building"][int(building_id)]
                new_system.bd = building

                # Add remaining parameters
                ignore_list = ["foundation_id", "building_id", "soil_profile_id"]
                add_to_obj(new_system, data_models[mtype][m_id], exceptions=ignore_list, verbose=verbose)
                objs[base_type][int(data_models[mtype][m_id]["id"])] = new_system

    all_bts = list(objs)
    for base_type in all_bts:  # Support for old style ecp file
        if base_type in standard_types:
            objs[base_type + "s"] = objs[base_type]
    return objs


class Output(object):
    name = ""
    units = ""
    doi = ""
    sfsimodels_version = ""
    comments = ""
    compression = True

    def __init__(self):
        self.unordered_models = OrderedDict()

    def add_to_dict(self, an_object, extras=None):
        """
        Convert models to json serialisable output

        :param an_object: An instance of a model object
        :param extras: A dictionary of extra variables that should be
        :return:
        """
        if an_object.id is None:
            raise ModelError("id must be set on object before adding to output.")
        if hasattr(an_object, "base_type"):
            mtype = an_object.base_type
        elif hasattr(an_object, "type"):
            if an_object.type in standard_types:
                mtype = an_object.type
            else:
                mtype = "custom_type"
        else:
            raise ModelError("Object does not have attribute 'base_type' or 'type', cannot add to output.")
        if mtype not in self.unordered_models:  # Catch any custom objects
            self.unordered_models[mtype] = OrderedDict()
        if mtype == "soil_profile":
            if "soil" not in self.unordered_models:
                self.unordered_models["soil"] = OrderedDict()
            profile_dict = an_object.to_dict()
            profile_dict["layers"] = []
            for layer in an_object.layers:
                self.unordered_models["soil"][an_object.layers[layer].id] = an_object.layers[layer].to_dict()
                profile_dict["layers"].append({
                    "soil_id": str(an_object.layers[layer].id),
                    "depth": float(layer)
                })

            self.unordered_models["soil_profile"][an_object.id] = profile_dict
        elif hasattr(an_object, "to_dict"):
            self.unordered_models[mtype][an_object.id] = an_object.to_dict(compression=self.compression)
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
        if mtype not in self.unordered_models:
            self.unordered_models[mtype] = OrderedDict()
        self.unordered_models[mtype][m_id] = serialisable_dict

    @property
    def models(self):
        models_dict = OrderedDict()
        collected = []
        for item in standard_types:
            if item in self.unordered_models:
                models_dict[item] = self.unordered_models[item]
                collected.append(item)
        for item in self.unordered_models:
            if item not in collected:
                models_dict[item] = self.unordered_models[item]
        return models_dict

    @staticmethod
    def parameters():
        return ["name", "units", "doi", "sfsimodels_version", "comments", "models"]

    def to_dict(self):
        outputs = OrderedDict()
        for item in self.parameters():
            outputs[item] = self.__getattribute__(item)
        return outputs
