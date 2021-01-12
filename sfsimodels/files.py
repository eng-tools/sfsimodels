import json

from sfsimodels.models import soils, buildings, foundations, systems, abstract_models, loads, materials, sections
from collections import OrderedDict
from sfsimodels.functions import add_to_obj
from sfsimodels.exceptions import deprecation, ModelError
from sfsimodels.__about__ import __version__
import numpy as np
from inspect import signature


standard_types = ["soil", "soil_profile", "foundation", "building", "section", "system", "custom_type"]


def _json_default(o):
    """Converts numpy types to json serialisable python types"""
    if isinstance(o, np.int64):
        return int(o)
    raise TypeError


def load_json(ffp, custom=None, default_to_base=False, verbose=0):
    """
    Given a json file it creates a dictionary of sfsi objects

    :param ffp: str, Full file path to json file
    :param custom: dict, used to load custom objects, {model type: custom object}
    :param verbose: int, console output
    :return: dict
    """
    data = json.load(open(ffp))
    return ecp_dict_to_objects(data, custom, default_to_base=default_to_base, verbose=verbose)


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


def get_matching_args_and_kwargs(in_dict, sm_obj, custom=None, overrides=None):
    if custom is None:
        custom = {}
    if overrides is None:
        overrides = {}
    sig = signature(sm_obj)
    kwargs = OrderedDict()
    args = []
    missing = []
    sig_vals = sig.parameters.values()
    for p in sig_vals:
        if p.name in custom:
            pname = custom[p.name]
        else:
            pname = p.name
        if pname == 'kwargs':
            continue
        if pname in overrides:
            val = overrides[pname]
        else:
            try:
                val = in_dict[pname]
            except KeyError as e:
                if p.default == p.empty:
                    missing.append((pname, len(args)))
                    val = None  # needs to be replaced
                else:
                    val = p.default
        if p.default == p.empty:
            args.append(val)
        else:
            if val is not None:
                kwargs[p.name] = val
    return args, kwargs, missing


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

def get_std_obj_map():
    obj_map = {
        "soil-soil": soils.Soil,
        "soil-critical_soil": soils.CriticalSoil,
        "soil-soil_critical": soils.CriticalSoil,  # deprecated type
        "soil-stress_dependent_soil": soils.StressDependentSoil,
        "soil-soil_stress_dependent": soils.StressDependentSoil,
        "soil_profile-soil_profile": soils.SoilProfile,
        "beam_column_element-beam_column_element": buildings.BeamColumnElement,
        "section-section": sections.Section,
        "section-rc_beam_section": sections.RCBeamSection,
        "building-building": buildings.Building,
        "building-null_building": buildings.NullBuilding,
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
        "foundation-pad_footing": foundations.PadFooting,
        "foundation-strip_foundation": foundations.StripFoundation,
        "custom_object-custom_object": abstract_models.CustomObject,
        "system-system": systems.SoilStructureSystem,  # deprecated type
        "system-sfs": systems.SoilStructureSystem,
        "system-two_d_system": systems.TwoDSystem,
        "load-load": loads.Load,
        "load-load_at_coords": loads.LoadAtCoords,
        "material-rc_material": materials.ReinforcedConcreteMaterial
    }
    return obj_map

def ecp_dict_to_objects(ecp_dict, custom_map=None, default_to_base=False, verbose=0):
    """
    Given an ecp dictionary, build a dictionary of sfsi objects

    :param ecp_dict: dict, engineering consistency project dictionary
    :param custom: dict, used to load custom objects, {model type: custom object}
    :param verbose: int, console output
    :return: dict
    """
    if custom_map is None:
        custom_map = {}

    obj_map = get_std_obj_map()
    # merge and overwrite the object map with custom maps
    # for item in custom_map:
    #     obj_map[item] = custom_map[item]
    obj_map = {**obj_map, **custom_map}

    data_models = ecp_dict["models"]

    exception_list = []
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
    load_later = {}
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
                if default_to_base and f'{base_type}-{base_type}' in obj_map:
                    obj_class = obj_map[f'{base_type}-{base_type}']
                elif obj["type"] in deprecated_types:
                    try:
                        obj_class = obj_map["%s-%s" % (base_type, deprecated_types[obj["type"]])]
                    except KeyError:
                        raise KeyError("Map for Model: '%s' index: '%s' and type: '%s' not available, "
                                       "add '%s-%s' to custom dict" % (base_type, m_id, base_type, base_type, obj["type"]))
                else:
                    raise KeyError("Map for Model: '%s' index: '%s' and type: '%s' not available, "
                                   "add '%s-%s' to custom dict" % (base_type, m_id, base_type, base_type, obj["type"]))
            # try:
            args, kwargs, missing = get_matching_args_and_kwargs(data_models[mtype][m_id], obj_class)
            if len(missing):
                for m_item in missing:
                    name = m_item[0]
                    m_indy = m_item[1]
                    if name == 'n_storeys':
                        args[m_indy] = len(data_models[mtype][m_id]["storey_masses"])
                    elif name == 'n_bays':
                        args[m_indy] = len(data_models[mtype][m_id]["bay_lengths"])
            new_instance = obj_class(*args, **kwargs)
            try:
                add_to_obj(new_instance, data_models[mtype][m_id], objs=objs, verbose=verbose)
            except KeyError as e:
                if hasattr(new_instance, 'loading_pre_reqs'):
                    if new_instance.base_type not in load_later:
                        load_later[new_instance.base_type] = []
                    load_later[new_instance.base_type].append([new_instance, data_models[mtype][m_id], verbose])
                    continue
                else:
                    raise KeyError(e)
            # print(mtype, m_id)
            objs[base_type][int(data_models[mtype][m_id]["id"])] = new_instance
    ll_types = list(load_later)
    now_loaded = []
    for ll_type in ll_types:
        if ll_type not in now_loaded:
            load_last_objects(objs, load_later, ll_type, now_loaded)


    # Deal with all the exceptions
    # for mtype in data_models:
    #     base_type = mtype
    #
    #     if base_type in collected:
    #         continue
    #     if base_type not in objs:
    #         objs[base_type] = OrderedDict()

    all_bts = list(objs)
    for base_type in all_bts:  # Support for old style ecp file
        if base_type in standard_types:
            objs[base_type + "s"] = objs[base_type]
    return objs


def load_last_objects(objs, load_later, ll_type, now_loaded):
    # if ll_type not in load_later:
    ll_objs = load_later[ll_type]
    for obj_pms in ll_objs:
        for pre_req in obj_pms[0].loading_pre_reqs:
            if pre_req in load_later and pre_req not in now_loaded:
                load_last_objects(objs, load_later, pre_req, now_loaded)  # could get into infinite loop if prereqs dependent on each other
        add_to_obj(obj_pms[0], obj_pms[1], objs=objs, verbose=obj_pms[2])
        objs[ll_type][int(obj_pms[1]["id"])] = obj_pms[0]
        now_loaded.append(ll_type)


class Output(object):
    name = ""
    units = None
    global_units = None
    doi = ""
    comments = ""
    compression = True
    reset_ids = True

    def __init__(self):
        self.unordered_models = {}
        self.id2hash_dict = {}

    @property
    def sfsimodels_version(self):
        return __version__

    @sfsimodels_version.setter
    def sfsimodels_version(self, value):
        deprecation('sfsimodels_version automatically set')

    def add_to_dict(self, an_object, export_none=False, extras=None):
        """
        Convert models to json serialisable output

        :param an_object: An instance of a model object
        :param extras: A dictionary of extra variables that should be
        :return:
        """
        if an_object.id is None and self.reset_ids is False:
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
            self.unordered_models[mtype] = {}

        if hasattr(an_object, "add_to_dict"):
            an_object.add_to_dict(self.unordered_models, export_none=export_none)

        elif hasattr(an_object, "to_dict"):
            self.unordered_models[mtype][an_object.unique_hash] = an_object.to_dict(compression=self.compression,
                                                                                    export_none=export_none)
        else:
            raise ModelError("Object does not have method 'to_dict', cannot add to output.")

    def build_id2hash_dict(self):
        for mtype in self.unordered_models:
            if mtype not in self.id2hash_dict:  # Catch any custom objects
                self.id2hash_dict[mtype] = OrderedDict()
            for unique_hash in self.unordered_models[mtype]:
                if self.reset_ids is False:
                    obj_id = self.unordered_models[mtype][unique_hash]['id']
                    if obj_id in self.id2hash_dict[mtype]:
                        raise ModelError('Duplicate id: {0} for model type: {1}'.format(obj_id, mtype))
                else:
                    obj_id = len(self.id2hash_dict[mtype]) + 1
                self.id2hash_dict[mtype][obj_id] = unique_hash

    def get_id_from_hash(self, mtype, unique_hash):
        for m_id in self.id2hash_dict[mtype]:
            if self.id2hash_dict[mtype][m_id] == unique_hash:
                return m_id
        return None

    def _replace_single_id(self, value, item, pdict=None):  # returns value
        """
        A recursive method to cycle through output dictionary and replace ids with the correct id in the id2hash_dict

        :param value:
        :param item:
        :param pdict:
        :return:
        """
        if isinstance(value, str):
            pass
        elif hasattr(value, '__len__'):
            tolist = getattr(value, "tolist", None)
            if hasattr(value, 'keys'):
                # odict = OrderedDict()
                for i2 in value:
                    self._replace_single_id(value[i2], i2, value)
                return value
            elif callable(tolist):
                values = value.tolist()
            else:
                values = value
            for i, val2 in enumerate(values):
                values[i] = self._replace_single_id(val2, '')  # if it is a list then check if dict is deeper
            return values
        if '_unique_hash' in item:  # detect link to new object
            child_mtype = item.replace('_unique_hash', '')
            child_hash = value
            pdict['{0}_id'.format(child_mtype)] = self.get_id_from_hash(child_mtype, child_hash)
        return value

    def replace_conflicting_ids(self):
        """
        Goes through output dictionary and replaces all ids with the correct id from the id2hash_dict

        :return:
        """
        self.build_id2hash_dict()
        for mtype in self.unordered_models:
            for unique_hash in self.unordered_models[mtype]:
                umd = self.unordered_models[mtype][unique_hash]
                umd['id'] = self.get_id_from_hash(mtype, unique_hash)
                for item in umd:
                    val = umd[item]
                    umd[item] = self._replace_single_id(val, item, umd)

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

    def get_models(self):
        """Unhashed"""
        self.replace_conflicting_ids()
        models_dict = OrderedDict()
        collected = []
        for item in standard_types:
            if item in self.unordered_models:
                new_dict, replacement_dict = unhash_dict(self.unordered_models[item])
                models_dict[item] = new_dict
                collected.append(item)
        for item in self.unordered_models:
            # print("item: ", item)
            if item not in collected:
                new_dict, replacement_dict = unhash_dict(self.unordered_models[item])
                models_dict[item] = new_dict
        return models_dict

    @staticmethod
    def parameters():
        return ["name", "units", "doi", "sfsimodels_version", "comments", "models"]

    def to_dict(self):
        outputs = OrderedDict()
        for item in self.parameters():
            if item == 'models':
                outputs[item] = self.get_models()
            else:
                outputs[item] = self.__getattribute__(item)
        return outputs

    def to_file(self, ffp, indent=4, name=None, units=None, comments=None):
        """Export to json file"""
        if name is not None:
            self.name = "%s" % name
        if units is not None:
            self.units = units
        if comments is not None:
            self.comments = comments
        json.dump(self.to_dict(), open(ffp, "w"), indent=indent, default=_json_default)

    def to_str(self, indent=4, name=None, units=None, comments=None):
        """Return as a json string"""
        if name is not None:
            self.name = "%s" % name
        if units is not None:
            self.units = units
        if comments is not None:
            self.comments = comments
        return json.dumps(self.to_dict(), indent=indent, default=_json_default)


def migrate_ecp(in_ffp, out_ffp):
    """Migrates and ECP file to the current version of sfsimodels"""
    objs, meta_data = load_json_and_meta(in_ffp)
    ecp_output = Output()
    for m_type in objs:
        for instance in objs[m_type]:
            ecp_output.add_to_dict(objs[m_type][instance])
    ecp_output.name = meta_data["name"]
    ecp_output.units = meta_data["units"]
    ecp_output.comments = meta_data["comments"]
    p_str = json.dumps(ecp_output.to_dict(), skipkeys=["__repr__"], indent=4)
    a = open(out_ffp, "w")
    a.write(p_str)
    a.close()


def unhash_dict(pdict):  # TODO: make method
    new_dict = OrderedDict()
    replacement_dict = OrderedDict()
    for i, item in enumerate(pdict):
        key = str(i + 1)
        # assert int(item) > 1000  # avoid hashes that are in the same range as ids!
        new_dict[key] = pdict[item]
        replacement_dict[item] = key
    return new_dict, replacement_dict


def _load_mod_dat():
    import os
    folder_path = os.path.dirname(os.path.realpath(__file__))
    return open(os.path.join(folder_path, 'models_data.dat'))
