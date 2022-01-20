from collections import OrderedDict

import numpy as np

from sfsimodels.models.abstract_models import PhysicalObject
# from sfsimodels.models import SeismicHazard, Foundation, Soil
from sfsimodels.exceptions import ModelError, deprecation
from sfsimodels import functions as sf
from sfsimodels.models.sections import Section


class Building(PhysicalObject):
    """
    An object to define Buildings

    Parameters
    ----------
    n_storeys : int
        Number of storeys

    """
    _id = None
    name = None
    base_type = "building"
    type = "building"
    _floor_length = None
    _floor_width = None
    _interstorey_heights = np.array([0.0])  # m
    _storey_masses = np.array([0.0])  # kg
    _n_storeys = None
    _g = 9.81  # m/s2  # gravity
    _foundation = None
    x_fd = None
    z_fd = None
    loading_pre_reqs = ('material',)

    def __init__(self, n_storeys, verbose=0, **kwargs):
        super(Building, self).__init__()
        self._n_storeys = n_storeys
        if not hasattr(self, "inputs"):
            self.inputs = []
        self._extra_class_variables = [
                "id",
                "name",
                "base_type",
                "type",
                'n_storeys',
                'floor_length',
                'floor_width',
                'interstorey_heights',
                'storey_masses',
                'foundation_id',
                'x_fd',
                'z_fd',
                'material'
            ]
        self.material = None
        self.inputs += self._extra_class_variables
        self.all_parameters = self.inputs + [
        ]

    def add_to_dict(self, models_dict, return_mdict=False, **kwargs):
        if self.base_type not in models_dict:
            models_dict[self.base_type] = OrderedDict()
        mdict = self.to_dict(**kwargs)
        if self.material is not None:
            if "material" not in models_dict:
                models_dict["material"] = OrderedDict()
            models_dict["material"][self.material.unique_hash] = self.material.to_dict(**kwargs)
            # mdict["material"] = {
            mdict['material_id'] = self.material.id
            mdict['material_unique_hash'] = self.material.unique_hash

        if return_mdict:
            return mdict
        models_dict[self.base_type][self.unique_hash] = mdict

    @property
    def ancestor_types(self):
        return super(Building, self).ancestor_types + ["building"]

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        if value not in [None, ""]:
            self._id = int(value)

    @property
    def floor_length(self):
        return self._floor_length

    @floor_length.setter
    def floor_length(self, value):
        self._floor_length = value

    @property
    def floor_width(self):
        return self._floor_width

    @floor_width.setter
    def floor_width(self, value):
        self._floor_width = value

    @property
    def g(self):
        return self._g

    @property
    def floor_area(self):
        try:
            return self.floor_length * self.floor_width
        except TypeError:
            return None

    @property
    def heights(self):
        return np.cumsum(self._interstorey_heights)

    @property
    def max_height(self):
        return np.sum(self._interstorey_heights)

    @property
    def n_storeys(self):
        return self._n_storeys

    @n_storeys.setter
    def n_storeys(self, value):
        assert self._n_storeys == value

    @property
    def interstorey_heights(self):
        return self._interstorey_heights

    @interstorey_heights.setter
    def interstorey_heights(self, heights):
        if len(heights) != self.n_storeys:
            raise ModelError("Specified heights must match number of storeys (%i)." % self.n_storeys)
        self._interstorey_heights = np.array(heights)

    @property
    def storey_masses(self):
        return self._storey_masses

    @storey_masses.setter
    def storey_masses(self, masses):
        self._storey_masses = np.array(masses)

    def set_storey_masses_by_pressure(self, stresses):
        if hasattr(stresses, "length"):
            if len(stresses) != self.n_storeys:
                raise ModelError("Length of defined storey pressures: {0}, "
                                 "must equal number of stories: {1}".format(len(stresses), self.n_storeys))
            self.storey_masses = stresses * self.floor_area / self._g
        else:
            self.storey_masses = stresses * np.ones(self.n_storeys) * self.floor_area / self._g

    @property
    def foundation(self):
        return self._foundation

    @property
    def fd(self):
        return self._foundation

    def set_foundation(self, foundation, x=None, z=None, two_way=True):
        """
        Connect a foundation to the building at position (x, y)

        Parameters
        ----------
        foundation: sm.Foundation
            Foundation object to be connected
        x: float
            Offset along x-axis of foundation centre line compared to building centre line
            (+ve is foundation to right of centre)
        z: float
            Offset along z-axis of foundation centre line compared to building centre line
                (+ve is foundation to front of centre)
        two_way

        Returns
        -------

        """
        if two_way:
            foundation.set_building(self, x=x, z=z, two_way=False)  # set false to avoid infinite loop
        if x is not None:
            self.x_fd = float(x)
        if z is not None:
            self.z_fd = float(z)
        self._foundation = foundation

    @property
    def foundation_id(self):
        if self._foundation is None:
            return None
        return self._foundation.id


class BeamColumnElement(PhysicalObject):
    base_type = "beam_column_element"
    type = "beam_column_element"
    section_lengths = None
    loading_pre_reqs = ('section',)

    def __init__(self, n_sects=1, section_class=None):
        self.inputs = ['type', 'base_type', 'sections']
        if section_class is None:
            self._sections = [Section() for i in range(n_sects)]
        else:
            self._sections = [section_class() for i in range(n_sects)]

    @property
    def s(self):
        return self._sections

    @property
    def sections(self):
        return self._sections

    @sections.setter
    def sections(self, sections):
        self._sections = []
        for section in sections:
            if isinstance(section, dict):
                self._sections.append(section['section'])  # load from ecp file
            else:
                self._sections.append(section)

    def set_section_prop(self, prop, prop_value, sections=None):
        if sections is None:
            sections = range(len(self.sections))
            prop_value = [prop_value] * len(self.sections)
        if isinstance(prop_value, str) or not hasattr(prop_value, '__len__'):
            prop_value = [prop_value] * len(self.sections)
        for i, sect_i in enumerate(sections):
            if not hasattr(self.sections[sect_i], prop) and prop not in self.sections[sect_i].inputs:
                self.sections[sect_i].inputs.append(prop)
            setattr(self.sections[sect_i], prop, prop_value[i])

    def add_inputs_to_section(self, props, sections=None):
        if sections is None:
            sections = range(len(self.sections))
        for sect_i in sections:
            self.sections[sect_i].inputs += props

    def split_into_multiple(self, lengths):
        section = self.sections[0]
        self.section_lengths = []
        self.sections = []
        for length in lengths:
            self.section_lengths.append(length)
            self.sections.append(section.deepcopy())

    def get_section_prop(self, prop, section_i=0):
        return getattr(self.sections[section_i], prop)

    def add_to_dict(self, models_dict, **kwargs):
        if self.base_type not in models_dict:
            models_dict[self.base_type] = OrderedDict()
        if "section" not in models_dict:
            models_dict["section"] = OrderedDict()
        mdict = self.to_dict(**kwargs)
        mdict["sections"] = []
        for i, section in enumerate(self.sections):
            if hasattr(self.sections[i], 'add_to_dict'):
                self.sections[i].add_to_dict(models_dict, **kwargs)
            else:
                models_dict["section"][self.sections[i].unique_hash] = self.sections[i].to_dict(**kwargs)
            mdict["sections"].append({
                "section_id": str(i),
                "section_unique_hash": str(self.sections[i].unique_hash),
                # "depth": float(section)
            })
        models_dict[self.base_type][self.unique_hash] = mdict


class Element(BeamColumnElement):
    pass

class WallElement(BeamColumnElement):
    type = "wall_element"
    def __init__(self, n_sects=1, section_class=None):
        # run parent class initialiser function
        super(WallElement, self).__init__(n_sects=n_sects, section_class=section_class)



class Frame(object):
    _bay_lengths = None
    _custom_beam_section = None
    _custom_column_section = None
    _loaded_beam_section_ids = None  # should not be accessed by end user
    _loaded_beam_sections = None  # should not be accessed by end user
    _loaded_column_section_ids = None  # should not be accessed by end user
    _loaded_column_sections = None  # should not be accessed by end user
    loading_pre_reqs = ('beam_column_element', )

    def __init__(self, n_storeys, n_bays):
        if not hasattr(self, "inputs"):
            self.inputs = []
        self._extra_class_variables = [
            "n_bays",
            "n_storeys",
            "beams",
            "columns",
            "bay_lengths"
        ]
        self.inputs += self._extra_class_variables
        self._n_storeys = n_storeys
        self._n_bays = n_bays
        self._allocate_beams_and_columns()

    def add_to_dict(self, models_dict, return_mdict=False, **kwargs):
        if self.base_type not in models_dict:
            models_dict[self.base_type] = OrderedDict()
        if "beam_column_element" not in models_dict:
            models_dict["beam_column_element"] = OrderedDict()
        mdict = self.to_dict(**kwargs)
        mdict["beams"] = []
        for i, storey in enumerate(self.beams):
            mdict["beams"].append([])
            for j, beam in enumerate(storey):
                self.beams[i][j].add_to_dict(models_dict, **kwargs)
                mdict["beams"][i].append({
                    "beam_column_element_id": str(i),
                    "beam_column_element_unique_hash": str(self.beams[i][j].unique_hash),
                    # "depth": float(section)
                })
        mdict["columns"] = []
        for i, storey in enumerate(self.columns):
            mdict["columns"].append([])
            for j, col in enumerate(storey):
                self.columns[i][j].add_to_dict(models_dict, **kwargs)
                mdict["columns"][i].append({
                    "beam_column_element_id": str(i),
                    "beam_column_element_unique_hash": str(self.columns[i][j].unique_hash),
                    # "depth": float(section)
                })
        if return_mdict:
            return mdict
        models_dict[self.base_type][self.unique_hash] = mdict

    def to_dict(self, extra=(), **kwargs):
        outputs = OrderedDict()
        skip_list = []
        skip_list = ["beams", "columns"]
        # skip_list = ["beams"]
        full_inputs = self.inputs + list(extra)
        for item in full_inputs:
            if item not in skip_list:
                value = self.__getattribute__(item)
                outputs[item] = sf.collect_serial_value(value)

        # # Deal with sections
        # beam_sections = OrderedDict()
        # beam_section_ids = []
        # beam_section_count = 1
        # for ss in range(self.n_storeys):
        #     beam_section_ids.append([])
        #     for bb in range(self.n_bays):
        #         beam_section_ids.append(beam_section_count)
        #         # build a hash string of the section inputs to check uniqueness
        #         parts = []
        #         for item in self.beams[ss][bb].inputs:
        #             parts.append(item)
        #             parts.append(getattr(self.beams[ss][bb], item))
        #         p_str = "-".join(parts)
        #         if p_str not in beam_sections:
        #             beam_sections[p_str] = self.beams[ss][bb].to_dict(extra)
        #             beam_sections[p_str]["id"] = beam_section_count
        #             beam_section_count += 1
        #
        # outputs["beam_section_ids"] = beam_section_ids
        # outputs["beam_sections"] = OrderedDict()
        # for i, p_str in enumerate(beam_sections):
        #     outputs["beam_sections"][beam_sections[p_str]["id"]] = beam_sections[p_str]
        return outputs

    @property
    def ancestor_types(self):
        return ["frame"]

    def _allocate_beams_and_columns(self):
        self._beams = np.array([[BeamColumnElement(section_class=self._custom_beam_section) for i in range(self.n_bays)] for ss in range(self.n_storeys)])
        self._columns = np.array([[BeamColumnElement(section_class=self._custom_column_section) for i in range(self.n_cols)] for ss in range(self.n_storeys)])

    @property
    def beams(self):
        return self._beams

    @beams.setter
    def beams(self, beams):
        for i, storey in enumerate(beams):
            for j, beam in enumerate(storey):
                if isinstance(beam, dict):
                    self._beams[i][j] = beam['beam_column_element']
                else:
                    self._beams[i][j] = beam

    @property
    def columns(self):
        return self._columns

    @columns.setter
    def columns(self, columns):
        for i, storey in enumerate(columns):
            for j, columns in enumerate(storey):
                if isinstance(columns, dict):
                    self._columns[i][j] = columns['beam_column_element']
                else:
                    self._columns[i][j] = columns

    @property
    def n_bays(self):
        return self._n_bays

    @n_bays.setter
    def n_bays(self, value):
        assert self._n_bays == value

    def get_n_cols(self):
        return self.n_bays + 1

    @property
    def n_storeys(self):
        return self._n_storeys

    @n_storeys.setter
    def n_storeys(self, value):
        assert self._n_storeys == value

    @property
    def n_cols(self):
        return self._n_bays + 1

    @property
    def beam_section_ids(self):
        return None

    @beam_section_ids.setter
    def beam_section_ids(self, beam_ids):
        self._loaded_beam_section_ids = beam_ids
        if self._loaded_beam_sections is not None:
            self._assign_loaded_beams()

    @property
    def beam_sections(self):
        return None

    @beam_sections.setter
    def beam_sections(self, beam_sections):
        self._loaded_beam_sections = beam_sections
        if self._loaded_beam_section_ids is not None:
            self._assign_loaded_beams()

    def _assign_loaded_beams(self):  # This is now deprecated in favour of element based loading
        for ss in range(self.n_storeys):
            for bb in range(self.n_bays):
                sect_is = self._loaded_beam_section_ids[ss][bb]
                if hasattr(sect_is, "__len__"):
                    n_sections = len(sect_is)
                    self.beams[ss][bb].split_into_multiple([1] * n_sections)  # TODO: should be lengths
                    for sect_i in range(len(sect_is)):
                        beam_sect_id = str(self._loaded_beam_section_ids[ss][bb][sect_i])
                        sect_dictionary = self._loaded_beam_sections[beam_sect_id]
                        sf.add_to_obj(self.beams[ss][bb].sections[sect_i], sect_dictionary)
                else:  # deprecated loading
                    deprecation("Frame data structure is out-of-date, please load and save the file to update.")
                    beam_sect_id = str(self._loaded_beam_section_ids[ss][bb])
                    sect_dictionary = self._loaded_beam_sections[beam_sect_id]
                    sf.add_to_obj(self.beams[ss][bb].sections[0], sect_dictionary)

    @property
    def column_section_ids(self):
        return None

    @column_section_ids.setter
    def column_section_ids(self, column_ids):
        self._loaded_column_section_ids = column_ids
        if self._loaded_column_sections is not None:
            self._assign_loaded_columns()

    @property
    def column_sections(self):
        return None

    @column_sections.setter
    def column_sections(self, column_sections):
        self._loaded_column_sections = column_sections
        if self._loaded_column_section_ids is not None:
            self._assign_loaded_columns()

    def _assign_loaded_columns(self):
        for ss in range(self.n_storeys):
            for bb in range(self.n_bays):
                sect_is = self._loaded_column_section_ids[ss][bb]
                if hasattr(sect_is, "__len__"):
                    n_sections = len(sect_is)
                    self.columns[ss][bb].split_into_multiple([1] * n_sections)  # TODO: should be lengths
                    for sect_i in range(len(sect_is)):
                        column_sect_id = str(self._loaded_column_section_ids[ss][bb][sect_i])
                        sect_dictionary = self._loaded_column_sections[column_sect_id]
                        sf.add_to_obj(self.columns[ss][bb].sections[sect_i], sect_dictionary)
                else:  # deprecated loading
                    deprecation("Frame data structure is out-of-date, "
                                "run sfsimodels.migrate_ecp(<file-path>, <out-file-path>).")
                    column_sect_id = str(self._loaded_column_section_ids[ss][bb])
                    sect_dictionary = self._loaded_column_sections[column_sect_id]
                    sf.add_to_obj(self.columns[ss][bb].sections[0], sect_dictionary)

    def set_beam_prop(self, prop, values, repeat="up", sections=None):
        """
        Specify the properties of the beam

        Parameters
        ----------
        prop: str
            Name of property that values should be assigned to
        values: value or array_like
            Value or list of values to be assigned
        repeat: str
            If 'up' then duplicate up the structure, if 'all' the duplicate for all columns
        """
        si = 0
        if sections is not None:
            si = 1
        values = np.array(values)
        if repeat == "up":
            assert len(values.shape) == 1 + si
            values = [values for ss in range(self.n_storeys)]
        elif repeat == "all":
            assert len(values.shape) == 0 + si
            values = [[values for i in range(self.n_bays)] for ss in range(self.n_storeys)]
        else:
            assert len(values.shape) == 2 + si
        if len(values[0]) != self.n_bays:
            raise ModelError("beam depths does not match number of bays (%i)." % self.n_bays)
        for ss in range(self.n_storeys):
            for i in range(self.n_bays):
                self._beams[ss][i].set_section_prop(prop, values[ss][i], sections=sections)

    def set_column_prop(self, prop, values, repeat="up", sections=None):
        """
        Specify the properties of the columns

        Parameters
        ----------
        prop: str
            Name of property that values should be assigned to
        values: value or array_like
            Value or list of values to be assigned
        repeat: str
            If 'up' then duplicate up the structure, if 'all' the duplicate for all columns
        """
        si = 0
        if sections is not None:
            si = 1
        values = np.array(values)
        if repeat == "up":
            assert len(values.shape) == 1 + si
            values = [values for ss in range(self.n_storeys)]
        elif repeat == 'all':
            assert len(values.shape) == 0 + si
            values = [[values for i in range(self.n_cols)] for ss in range(self.n_storeys)]
        else:
            assert len(values.shape) == 2 + si
        if len(values[0]) != self.n_cols:
            raise ModelError("column props does not match n_cols (%i)." % self.n_cols)
        for ss in range(self.n_storeys):
            for i in range(self.n_cols):
                self._columns[ss][i].set_section_prop(prop, values[ss][i], sections=sections)

    def beams_at_storey(self, storey):
        """Get the beams at a particular storey"""
        return self._beams[storey - 1]

    def get_beams_at_storey(self, storey):
        """Get the beams at a particular storey"""
        return self._beams[storey - 1]

    @property
    def beam_depths(self):
        """Get a 2D array of beam depths, first index is storey"""
        beam_depths = []
        for ss in range(self.n_storeys):
            beam_depths.append([])
            for i in range(self.n_bays):
                beam_depths[ss].append(self.beams[ss][i].get_section_prop("depth"))
        return np.array(beam_depths)

    @property
    def beam_widths(self):
        """Get a 2D array of beam widths, first index is storey"""
        beam_widths = []
        for ss in range(self.n_storeys):
            beam_widths.append([])
            for i in range(self.n_bays):
                beam_widths[ss].append(self.beams[ss][i].get_section_prop("width"))
        return np.array(beam_widths)

    @property
    def column_depths(self):
        """Get a 2D array of column depths, first index is storey"""
        column_depths = []
        for ss in range(self.n_storeys):
            column_depths.append([])
            for i in range(self.n_cols):
                column_depths[ss].append(self.columns[ss][i].get_section_prop("depth"))
        return np.array(column_depths)

    @property
    def column_widths(self):
        """Get a 2D array of column widths, first index is storey"""
        column_widths = []
        for ss in range(self.n_storeys):
            column_widths.append([])
            for i in range(self.n_cols):
                column_widths[ss].append(self.columns[ss][i].get_section_prop("width"))
        return np.array(column_widths)

    @property
    def bay_lengths(self):
        return self._bay_lengths

    @bay_lengths.setter
    def bay_lengths(self, bay_lengths):
        if len(bay_lengths) != self.n_bays:
            raise ModelError("bay_lengths does not match number of bays (%i)." % self.n_bays)
        self._bay_lengths = np.array(bay_lengths)

    def get_column_positions(self):  # could override in frame building if floor length is longer than bay lengths

        return np.cumsum(np.pad(self.bay_lengths, (1, 0), "constant")) - np.sum(self.bay_lengths) / 2


class FrameBuilding(Frame, Building):
    _n_seismic_frames = None
    _n_gravity_frames = None
    type = "frame_building"

    def __init__(self, n_storeys, n_bays):
        """
        A building that has frames aligned along the length axis

        :param n_storeys:
        :param n_bays:
        """
        Frame.__init__(self, n_storeys, n_bays)
        Building.__init__(self, n_storeys)
        # super(BuildingFrame, self).__init__(n_storeys, n_bays)  # run parent class initialiser function
        self._extra_class_inputs = ["n_seismic_frames",
                           "n_gravity_frames",
                                    "horz2vert_mass"]
        self.inputs = self.inputs + self._extra_class_inputs
        self.horz2vert_mass = 1.0
        self.x_offset = 0.0  # distance between centre of frame and centre of floor
        # Frame.__init__(self, n_storeys, n_bays)
        # Building.__init__(self, n_storeys, n_bays)

    @property
    def ancestor_types(self):
        """List of ancestors class types"""
        return super(FrameBuilding, self).ancestor_types + ["frame_building"]

    @property
    def n_seismic_frames(self):
        """Number of seismically resisting frames"""
        return self._n_seismic_frames

    @n_seismic_frames.setter
    def n_seismic_frames(self, value):
        self._n_seismic_frames = value

    @property
    def n_gravity_frames(self):
        return self._n_gravity_frames

    @n_gravity_frames.setter
    def n_gravity_frames(self, value):
        self._n_gravity_frames = value

    @property
    def n_frames(self):
        return self.n_gravity_frames + self.n_seismic_frames

    def get_column_vert_loads(self):
        """
        Vertical loads at column bases

        return [len-axis][width-axis]
        :return:
        """
        n_total = np.sum(self.storey_masses) * 9.8
        edge = (self.floor_length - np.sum(self.bay_lengths)) / 2
        trib_lens = np.zeros(self.n_cols)
        trib_lens[0] = self.bay_lengths[0] / 2 + edge + self.x_offset
        trib_lens[-1] = self.bay_lengths[-1] / 2 + edge - self.x_offset
        trib_lens[1:-1] = (self.bay_lengths[1:] + self.bay_lengths[:-1]) / 2

        tw = self.floor_width / (self.n_frames - 1)
        trib_widths = tw * np.ones(self.n_frames + 1)
        trib_widths[0] = tw / 2
        trib_widths[-1] = tw / 2
        return n_total * (trib_lens[:, np.newaxis] * trib_widths[np.newaxis, :]) / self.floor_area

    def add_to_dict(self, models_dict, return_mdict=False, **kwargs):
        frame_mdict = Frame.add_to_dict(self, models_dict, return_mdict=True, **kwargs)
        building_mdict = Building.add_to_dict(self, models_dict, return_mdict=True, **kwargs)
        mdict = {**frame_mdict, **building_mdict}
        if return_mdict:
            return mdict
        models_dict[self.base_type][self.unique_hash] = mdict


class FrameBuilding2D(Frame, Building):
    _extra_class_inputs = []
    type = "frame_building2D"

    def __init__(self, n_storeys, n_bays):
        """
        A 2 dimensional definition of of frame building

        Parameters
        ----------
        n_storeys: int
            Number of storeys
        n_bays: int
            Number of bays
        """
        Frame.__init__(self, n_storeys, n_bays)
        Building.__init__(self, n_storeys)
        # super(FrameBuilding2D, self).__init__(n_storeys, n_bays)  # run parent class initialiser function
        self.inputs = self.inputs + self._extra_class_inputs

    @property
    def ancestor_types(self):
        return ["physical_object", "frame", "building"] + ["frame_building2D"]  # TODO: improve this logic

    def to_dict(self, extra=(), compression=True, **kwargs):
        outputs = OrderedDict()
        skip_list = ["beams", "columns"]
        full_inputs = self.inputs + list(extra)
        for item in full_inputs:
            if item not in skip_list:
                value = self.__getattribute__(item)
                outputs[item] = sf.collect_serial_value(value)

        # Deal with sections
        column_sections = OrderedDict()
        column_section_ids = []
        column_section_count = 0
        for ss in range(self.n_storeys):
            column_section_ids.append([])
            for cc in range(self.n_cols):

                column_section_ids[ss].append([])
                for sect_i in range(len(self.columns[ss][cc].sections)):
                    if compression:  # build a hash string of the section inputs to check uniqueness
                        parts = []
                        for item in self.columns[ss][cc].sections[sect_i].inputs:
                            if item == "id" or item == "name":
                                continue
                            parts.append(item)
                            parts.append(str(self.columns[ss][cc].get_section_prop(item, section_i=sect_i)))
                        p_str = "-".join(parts)
                    else:
                        p_str = str(sect_i)
                    if p_str not in column_sections:
                        column_sections[p_str] = self.columns[ss][cc].sections[sect_i].to_dict(extra)
                        column_section_count += 1
                        col_sect_id = column_section_count
                        column_sections[p_str]["id"] = col_sect_id
                    else:
                        col_sect_id = column_sections[p_str]["id"]
                    column_section_ids[ss][cc].append(col_sect_id)

        beam_sections = OrderedDict()
        beam_section_ids = []
        beam_section_count = 0
        for ss in range(self.n_storeys):
            beam_section_ids.append([])
            for bb in range(self.n_bays):
                beam_section_ids[ss].append([])
                for sect_i in range(len(self.beams[ss][bb].sections)):
                    if compression:  # build a hash string of the section inputs to check uniqueness
                        parts = []
                        for item in self.beams[ss][bb].sections[sect_i].inputs:
                            if item == "id" or item == "name":
                                continue
                            parts.append(item)
                            parts.append(str(self.beams[ss][bb].get_section_prop(item, section_i=sect_i)))
                        p_str = "-".join(parts)
                    else:
                        p_str = str(sect_i)
                    if p_str not in beam_sections:
                        beam_sections[p_str] = self.beams[ss][bb].sections[sect_i].to_dict(extra)
                        beam_section_count += 1
                        beam_sect_id = beam_section_count
                        beam_sections[p_str]["id"] = beam_sect_id
                    else:
                        beam_sect_id = beam_sections[p_str]["id"]
                    beam_section_ids[ss][bb].append(beam_sect_id)

        outputs["column_section_ids"] = column_section_ids
        outputs["beam_section_ids"] = beam_section_ids
        outputs["column_sections"] = OrderedDict()
        outputs["beam_sections"] = OrderedDict()
        for i, p_str in enumerate(column_sections):
            outputs["column_sections"][column_sections[p_str]["id"]] = column_sections[p_str]
        for i, p_str in enumerate(beam_sections):
            outputs["beam_sections"][beam_sections[p_str]["id"]] = beam_sections[p_str]
        return outputs


class WallBuilding(Building):
    """
    A building with walls
    """
    n_walls = 1
    wall_depth = 0.0  # m
    wall_width = 0.0  # m
    type = "wall_building"

    def __init__(self, n_storeys):
        super(WallBuilding, self).__init__(n_storeys)  # run parent class initialiser function
        self._extra_class_inputs = [
            "n_walls",
            "wall_depth",
            "wall_width"
        ]
        self.inputs += self._extra_class_inputs

    @property
    def ancestor_types(self):
        return super(WallBuilding, self).ancestor_types + ["wall_building"]


class SDOFBuilding(PhysicalObject):
    """
    An object to describe structures.
    """
    _id = None
    name = None
    base_type = "building"
    type = "sdof"
    _h_eff = None
    _mass_eff = None
    _t_fixed = None
    _mass_ratio = None
    _foundation = None
    x_fd = None
    z_fd = None

    def __init__(self, g=9.8):
        self.inputs = [
            "id",
            "name",
            "base_type",
            "type",
            "h_eff",
            "mass_eff",
            "t_fixed",
            "mass_ratio",
            'foundation_id',
            'x_fd',
            'z_fd'
        ]
        self._g = g

    @property
    def ancestor_types(self):
        return super(SDOFBuilding, self).ancestor_types + ["sdof"]

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = int(value)

    @property
    def h_eff(self):
        return self._h_eff

    @h_eff.setter
    def h_eff(self, value):
        if value is None or value == "":
            return
        self._h_eff = float(value)

    @property
    def mass_eff(self):
        return self._mass_eff

    @mass_eff.setter
    def mass_eff(self, value):
        if value is None or value == "":
            return
        self._mass_eff = float(value)

    @property
    def t_fixed(self):
        return self._t_fixed

    @t_fixed.setter
    def t_fixed(self, value):
        if value is None or value == "":
            return
        self._t_fixed = float(value)

    @property
    def mass_ratio(self):
        return self._mass_ratio

    @mass_ratio.setter
    def mass_ratio(self, value):
        if value is None or value == "":
            return
        self._mass_ratio = float(value)

    @property
    def k_eff(self):
        return 4.0 * np.pi ** 2 * self.mass_eff / self.t_fixed ** 2

    @property
    def weight(self):
        return self.mass_eff / self.mass_ratio * self._g

    @property
    def foundation(self):
        return self._foundation

    @property
    def fd(self):
        return self._foundation

    @property
    def foundation_id(self):
        if self._foundation is None:
            return None
        return self._foundation.id

    def set_foundation(self, foundation, x=None, z=None, two_way=True):
        """
        Connect a foundation to the building at position (x, y)

        Parameters
        ----------
        foundation: sm.Foundation
            Foundation object to be connected
        x: float
            Offset along x-axis of foundation centre line compared to building centre line
            (+ve is foundation to right of centre)
        z: float
            Offset along z-axis of foundation centre line compared to building centre line
                (+ve is foundation to front of centre)
        two_way

        Returns
        -------

        """
        if two_way:
            foundation.set_building(self, x=x, z=z, two_way=False)  # set false to avoid infinite loop
        if x is not None:
            self.x_fd = float(x)
        if z is not None:
            self.z_fd = float(z)
        self._foundation = foundation


class NullBuilding(PhysicalObject):
    """
    A placeholder building

    Parameters
    ----------
    n_storeys : int
        Number of storeys

    """
    _id = None
    name = None
    base_type = "building"
    type = "null_building"
    _g = 9.81  # m/s2  # gravity
    _foundation = None
    x_fd = None
    z_fd = None

    def __init__(self, verbose=0, **kwargs):
        super(NullBuilding, self).__init__()
        if not hasattr(self, "inputs"):
            self.inputs = []
        self._extra_class_variables = [
            "id",
            "name",
            "base_type",
            "type",
            'foundation_id',
            'x_fd',
            'z_fd'
        ]
        self.inputs += self._extra_class_variables
        self.all_parameters = self.inputs + [
        ]

    @property
    def ancestor_types(self):
        return super(NullBuilding, self).ancestor_types + ["null_building"]

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        if value not in [None, ""]:
            self._id = int(value)

    @property
    def foundation(self):
        return self._foundation

    @property
    def fd(self):
        return self._foundation

    @property
    def foundation_id(self):
        if self._foundation is None:
            return None
        return self._foundation.id

    def set_foundation(self, foundation, x=None, z=None, two_way=True):
        """
        Connect a foundation to the building at position (x, y)

        Parameters
        ----------
        foundation: sm.Foundation
            Foundation object to be connected
        x: float
            Offset along x-axis of foundation centre line compared to building centre line
            (+ve is foundation to right of centre)
        z: float
            Offset along z-axis of foundation centre line compared to building centre line
                (+ve is foundation to front of centre)
        two_way

        Returns
        -------

        """
        if two_way:
            foundation.set_building(self, x=x, z=z, two_way=False)  # set false to avoid infinite loop
        if x is not None:
            self.x_fd = float(x)
        if z is not None:
            self.z_fd = float(z)
        self._foundation = foundation


class SingleWall(PhysicalObject):

    _custom_wall_section = None
    _loaded_wall_section_ids = None  # should not be accessed by end user
    _loaded_wall_sections = None  # should not be accessed by end user
    loading_pre_reqs = ('beam_column_element', )
    base_type = "building"
    type = "single_wall"
    g = 9.81  # m/s2  # gravity

    def __init__(self, n_storeys):
        if not hasattr(self, "inputs"):
            self.inputs = ["id",
                           "name",
                           "base_type",
                           "type",
                           'interstorey_heights',
                           'storey_masses',
                           'storey_n_loads',
                           'g']
        self._extra_class_variables = [
            "n_storeys",
            "elements"
        ]
        self.inputs += self._extra_class_variables
        self._n_storeys = n_storeys
        self.elements = []
        self._storey_n_loads = np.zeros(n_storeys)
        self._storey_masses = np.zeros(n_storeys)
        self._interstorey_heights = np.zeros(n_storeys)
        self._allocate_elements()

    def add_to_dict(self, models_dict, return_mdict=False, **kwargs):
        if self.base_type not in models_dict:
            models_dict[self.base_type] = OrderedDict()
        if "beam_column_element" not in models_dict:
            models_dict["beam_column_element"] = OrderedDict()
        mdict = self.to_dict(**kwargs)
        mdict["elements"] = []
        for i, storey in enumerate(self.elements):
            self.elements[i].add_to_dict(models_dict, **kwargs)
            mdict["elements"].append({
                "beam_column_element_id": str(i),
                "beam_column_element_unique_hash": str(self.elements[i].unique_hash),
                # "depth": float(section)
            })
        if return_mdict:
            return mdict
        models_dict[self.base_type][self.unique_hash] = mdict

    def to_dict(self, extra=(), **kwargs):
        outputs = OrderedDict()
        skip_list = ["elements"]
        full_inputs = self.inputs + list(extra)
        for item in full_inputs:
            if item not in skip_list:
                value = self.__getattribute__(item)
                outputs[item] = sf.collect_serial_value(value)

        return outputs

    @property
    def ancestor_types(self):
        return ["frame"]

    def _allocate_elements(self):
        self._elements = np.array([WallElement(section_class=self._custom_wall_section) for ss in range(self.n_storeys)])

    @property
    def elements(self):
        return self._elements

    @elements.setter
    def elements(self, elements):
        for i, ele in enumerate(elements):
            if isinstance(ele, dict):
                self._elements[i] = ele['beam_column_element']
            else:
                self._elements[i] = elements

    @property
    def n_storeys(self):
        return self._n_storeys

    @n_storeys.setter
    def n_storeys(self, value):
        assert self._n_storeys == value

    @property
    def interstorey_heights(self):
        return self._interstorey_heights

    @interstorey_heights.setter
    def interstorey_heights(self, heights):
        if len(heights) != self.n_storeys:
            raise ModelError("Specified heights must match number of storeys (%i)." % self.n_storeys)
        self._interstorey_heights = np.array(heights)

    @property
    def heights(self):
        return np.cumsum(self._interstorey_heights)

    @property
    def max_height(self):
        return np.sum(self._interstorey_heights)

    @property
    def storey_masses(self):
        return self._storey_masses

    @storey_masses.setter
    def storey_masses(self, masses):
        self._storey_masses = np.array(masses)

    @property
    def storey_n_loads(self):
        return self._storey_n_loads

    @storey_n_loads.setter
    def storey_n_loads(self, n_loads):
        self._storey_n_loads = np.array(n_loads)

    @property
    def wall_section_ids(self):
        return None

    @wall_section_ids.setter
    def element_section_ids(self, beam_ids):
        self._loaded_wall_section_ids = beam_ids
        if self._loaded_wall_sections is not None:
            self._assign_loaded_walls()

    @property
    def wall_sections(self):
        return None

    @wall_sections.setter
    def wall_sections(self, wall_sections):
        self._loaded_wall_sections = wall_sections
        if self._loaded_wall_section_ids is not None:
            self._assign_loaded_walls()

    def _assign_loaded_walls(self):  # This is now deprecated in favour of element based loading
        for ss in range(self.n_storeys):
            sect_is = self._loaded_wall_section_ids[ss]
            if hasattr(sect_is, "__len__"):
                n_sections = len(sect_is)
                self.elements[ss].split_into_multiple([1] * n_sections)  # TODO: should be lengths
                for sect_i in range(len(sect_is)):
                    wall_sect_id = str(self._loaded_wall_section_ids[ss][sect_i])
                    sect_dictionary = self._loaded_wall_sections[wall_sect_id]
                    sf.add_to_obj(self.elements[ss].sections[sect_i], sect_dictionary)
            else:  # deprecated loading
                deprecation("Frame data structure is out-of-date, please load and save the file to update.")
                wall_sect_id = str(self._loaded_wall_section_ids[ss])
                sect_dictionary = self._loaded_wall_sections[wall_sect_id]
                sf.add_to_obj(self.elements[ss].sections[0], sect_dictionary)

    def set_wall_prop(self, prop, values, repeat="up", sections=None):
        """
        Specify the properties of the beam

        Parameters
        ----------
        prop: str
            Name of property that values should be assigned to
        values: value or array_like
            Value or list of values to be assigned
        repeat: str
            If 'up' then duplicate up the structure, if 'all' the duplicate for all columns
        """
        si = 0
        if sections is not None:
            si = 1
        values = np.array(values)
        if repeat == "up":
            assert len(values.shape) == 0 + si
            values = [values for ss in range(self.n_storeys)]
        elif repeat == "all":
            assert len(values.shape) == 0 + si
            values = [values for ss in range(self.n_storeys)]
        else:
            assert len(values.shape) == 1 + si

        for ss in range(self.n_storeys):
            self._elements[ss].set_section_prop(prop, values[ss], sections=sections)

    @property
    def wall_depth(self):
        return self._elements[0].s[0].depth

    @wall_depth.setter
    def wall_depth(self, value):
        self.set_wall_prop('depth', value)

    @property
    def wall_width(self):
        return self._elements[0].s[0].width

    @wall_width.setter
    def wall_width(self, value):
        self.set_wall_prop('width', value)

#
# class SoilStructureSystem(PhysicalObject):
#     bd = SDOFBuilding()
#     fd = Foundation()
#     sp = Soil()
#     hz = SeismicHazard()
#     name = "Nameless"
#
#     inputs = ["name"] + bd.inputs + fd.inputs + sp.inputs + hz.inputs


