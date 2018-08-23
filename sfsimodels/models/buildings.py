from collections import OrderedDict

import numpy as np

from sfsimodels.models.abstract_models import PhysicalObject
from sfsimodels.models import SeismicHazard, Foundation, Soil
from sfsimodels.models.material import Concrete
from sfsimodels.exceptions import ModelError
from sfsimodels import functions as sf


class Building(PhysicalObject):
    """
    An object to define Buildings
    """
    _id = None
    name = None
    base_type = "building"
    type = "building"
    _floor_length = None
    _floor_width = None
    _interstorey_heights = np.array([0.0])  # m
    _storey_masses = np.array([0.0])  # kg
    _concrete = Concrete()
    _n_storeys = None
    _g = 9.81  # m/s2  # gravity

    def __init__(self, n_storeys, verbose=0, **kwargs):
        print(**kwargs)
        super(Building, self).__init__()
        self._n_storeys = n_storeys
        if not hasattr(self, "inputs"):
            self.inputs = []
        self._extra_class_variables = [
                "id",
                "name",
                "type",
                'floor_length',
                'floor_width',
                'interstorey_heights',
                'storey_masses'
            ]
        self.inputs += self._extra_class_variables
        self.all_parameters = self.inputs + [
            "n_storeys"
        ]

    def to_dict(self, extra=()):
        outputs = OrderedDict()
        skip_list = []
        full_inputs = self.inputs + list(extra)
        for item in full_inputs:
            if item not in skip_list:
                value = self.__getattribute__(item)
                outputs[item] = sf.collect_serial_value(value)
        return outputs

    @property
    def ancestor_types(self):
        return super(Building, self).ancestor_types + ["building"]

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

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
    def concrete(self):
        return self._concrete

    @concrete.setter
    def concrete(self, conc_inst):
        self._concrete = conc_inst

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


class Section(PhysicalObject):  # not used?
    id = None
    type = "section"
    base_type = "section"
    _depth = None
    _width = None

    def __init__(self):
        self.inputs = ["depth",
                       "width"]

    def to_dict(self, extra=()):
        outputs = OrderedDict()
        skip_list = []
        full_inputs = self.inputs + list(extra)
        for item in full_inputs:
            if item not in skip_list:
                value = self.__getattribute__(item)
                outputs[item] = sf.collect_serial_value(value)
        return outputs

    @property
    def depth(self):
        return self._depth

    @depth.setter
    def depth(self, value):
        self._depth = value

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        self._width = value


class Frame(object):
    _bay_lengths = None

    def __init__(self, n_storeys, n_bays):
        if not hasattr(self, "inputs"):
            self.inputs = []
        self._extra_class_variables = [
            "beams",
            "columns",
            "bay_lengths"
        ]
        self.inputs += self._extra_class_variables
        self._n_storeys = n_storeys
        self._n_bays = n_bays
        self._allocate_beams_and_columns()

    def to_dict(self, extra=()):
        outputs = OrderedDict()
        skip_list = []
        # skip_list = ["beams", "columns"]  # TODO: uncomment this
        skip_list = ["beams"]
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
        self._beams = [[Section() for i in range(self.n_bays)] for ss in range(self.n_storeys)]
        self._columns = [[Section() for i in range(self.n_cols)] for ss in range(self.n_storeys)]

    @property
    def beams(self):
        return self._beams

    @property
    def columns(self):
        return self._columns

    @property
    def n_bays(self):
        return self._n_bays

    @property
    def n_storeys(self):
        return self._n_storeys

    @property
    def n_cols(self):
        return self._n_bays + 1

    @n_bays.setter
    def n_bays(self, value):
        raise ModelError("Can not set n_bays, only on initialisation")

    # @column_sections.setter
    # def column_sections(self, columns: dict):
    #     assert len(columns) ==

    def set_beam_prop(self, prop, values, repeat="up"):
        """
        Specify the properties of the beams

        :param values:
        :param repeat: if 'up' then duplicate up the structure
        :return:
        """
        values = np.array(values)
        if repeat == "up":
            assert len(values.shape) == 1
            values = [values for ss in range(self.n_storeys)]
        else:
            assert len(values.shape) == 2
        if len(values[0]) != self.n_bays:
            raise ModelError("beam depths does not match number of bays (%i)." % self.n_bays)
        for ss in range(self.n_storeys):
            for i in range(self.n_bays):
                setattr(self._beams[ss][i], prop, values[0][i])

    def set_column_prop(self, prop, values, repeat="up"):
        """
        Specify the properties of the columns

        :param values:
        :param repeat: if 'up' then duplicate up the structure
        :return:
        """
        values = np.array(values)
        if repeat == "up":
            assert len(values.shape) == 1
            values = [values for ss in range(self.n_storeys)]
        else:
            assert len(values.shape) == 2
        if len(values[0]) != self.n_cols:
            raise ModelError("column props does not match n_cols (%i)." % self.n_cols)
        for ss in range(self.n_storeys):
            for i in range(self.n_cols):
                setattr(self._columns[ss][i], prop, values[0][i])

    def beams_at_storey(self, storey):
        return self._beams[storey - 1]

    @property
    def beam_depths(self):
        beam_depths = []
        for ss in range(self.n_storeys):
            beam_depths.append([])
            for i in range(self.n_bays):
                beam_depths[ss].append(self.beams[ss][i].depth)
        return np.array(beam_depths)

    @property
    def beam_widths(self):
        beam_widths = []
        for ss in range(self.n_storeys):
            beam_widths.append([])
            for i in range(self.n_bays):
                beam_widths[ss].append(self.beams[ss][i].width)
        return np.array(beam_widths)

    @property
    def column_depths(self):
        column_depths = []
        for ss in range(self.n_storeys):
            column_depths.append([])
            for i in range(self.n_cols):
                column_depths[ss].append(self.columns[ss][i].width)
        return np.array(column_depths)

    @property
    def column_widths(self):
        column_widths = []
        for ss in range(self.n_storeys):
            column_widths.append([])
            for i in range(self.n_cols):
                column_widths[ss].append(self.columns[ss][i].width)
        return np.array(column_widths)

    @property
    def bay_lengths(self):
        return self._bay_lengths

    @bay_lengths.setter
    def bay_lengths(self, bay_lengths):
        if len(bay_lengths) != self.n_bays:
            raise ModelError("bay_lengths does not match number of bays (%i)." % self.n_bays)
        self._bay_lengths = np.array(bay_lengths)


class FrameBuilding(Frame, Building):
    _n_seismic_frames = None
    _n_gravity_frames = None
    type = "frame_building"

    def __init__(self, n_storeys, n_bays):
        Frame.__init__(self, n_storeys, n_bays)
        Building.__init__(self, n_storeys)
        # super(FrameBuilding, self).__init__(n_storeys, n_bays)  # run parent class initialiser function
        self._extra_class_inputs = ["n_seismic_frames",
                           "n_gravity_frames"]
        self.inputs = self.inputs + self._extra_class_inputs
        # Frame.__init__(self, n_storeys, n_bays)
        # Building.__init__(self, n_storeys, n_bays)

    @property
    def ancestor_types(self):
        return super(FrameBuilding, self).ancestor_types + ["frame_building"]

    @property
    def n_seismic_frames(self):
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


class FrameBuilding2D(Frame, Building):
    _extra_class_inputs = []
    type = "frame_building_2D"

    def __init__(self, n_storeys, n_bays):
        Frame.__init__(self, n_storeys, n_bays)
        Building.__init__(self, n_storeys)
        # super(FrameBuilding2D, self).__init__(n_storeys, n_bays)  # run parent class initialiser function
        self.inputs = self.inputs + self._extra_class_inputs

    @property
    def ancestor_types(self):
        return ["physical_object", "frame", "building"] + ["frame_building_2D"]  # TODO: improve this logic

    # def to_dict(self, extra=()):
    #     outputs = OrderedDict()
    #     skip_list = []
    #     full_inputs = self.inputs + list(extra)
    #     for item in full_inputs:
    #         if item not in skip_list:
    #             value = self.__getattribute__(item)
    #             outputs[item] = sf.collect_serial_value(value)
    #     return outputs

    def to_dict(self, extra=()):
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
                # build a hash string of the section inputs to check uniqueness
                parts = []
                for item in self.columns[ss][cc].inputs:
                    parts.append(item)
                    parts.append(str(getattr(self.columns[ss][cc], item)))
                p_str = "-".join(parts)
                if p_str not in column_sections:
                    column_sections[p_str] = self.columns[ss][cc].to_dict(extra)
                    column_section_count += 1
                    column_sections[p_str]["id"] = column_section_count
                column_section_ids[ss].append(column_section_count)

        beam_sections = OrderedDict()
        beam_section_ids = []
        beam_section_count = 0
        for ss in range(self.n_storeys):
            beam_section_ids.append([])
            for bb in range(self.n_bays):
                # build a hash string of the section inputs to check uniqueness
                parts = []
                for item in self.beams[ss][bb].inputs:
                    parts.append(item)
                    parts.append(str(getattr(self.beams[ss][bb], item)))
                p_str = "-".join(parts)
                if p_str not in beam_sections:
                    beam_sections[p_str] = self.beams[ss][bb].to_dict(extra)
                    beam_section_count += 1
                    beam_sections[p_str]["id"] = beam_section_count
                beam_section_ids[ss].append(beam_section_count)

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


class Structure(PhysicalObject):
    """
    An object to describe structures.
    """
    _id = None
    name = None
    base_type = "building"
    type = "structure"
    _h_eff = None
    _mass_eff = None
    _t_fixed = None
    _mass_ratio = None

    inputs = [
        "id",
        "name",
        "base_type",
        "type",
        "h_eff",
        "mass_eff",
        "t_fixed",
        "mass_ratio"
    ]

    def __init__(self, g=9.8):
        self._g = g

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

    @property
    def ancestor_types(self):
        return super(Structure, self).ancestor_types + ["structure"]

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


class SoilStructureSystem(PhysicalObject):
    bd = Structure()
    fd = Foundation()
    sp = Soil()
    hz = SeismicHazard()
    name = "Nameless"

    inputs = ["name"] + bd.inputs + fd.inputs + sp.inputs + hz.inputs


if __name__ == '__main__':
    print(FrameBuilding2D.__mro__)
    a = FrameBuilding2D(1, 2)
    print(a.n_bays)
