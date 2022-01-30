from collections import OrderedDict
from sfsimodels.models import SoilProfile, Foundation, SDOFBuilding
from sfsimodels.exceptions import ModelError
from sfsimodels import functions as sf
import uuid
import numpy as np


class SoilStructureSystem(object):
    id = None
    name = None
    base_type = "system"
    type = "sfs"
    _unique_hash = None
    _sp = SoilProfile()
    _bd = SDOFBuilding()
    _fd = Foundation()
    _soil_profile_id = None
    _building_id = None
    _foundation_id = None

    def __init__(self):
        self.inputs = ["id", "name", "soil_profile_id", "building_id", "foundation_id"]

    def to_dict(self, **kwargs):
        outputs = OrderedDict()
        skip_list = []
        for item in self.inputs:
            if item not in skip_list:
                value = self.__getattribute__(item)
                if "_id" in item and value is None:
                    raise ModelError("Cannot export system with %s set to None" % item)
                if item not in skip_list:
                    value = self.__getattribute__(item)
                    outputs[item] = sf.collect_serial_value(value)
        return outputs

    def add_obj_to_system(self, obj):
        if hasattr(obj, "base_type"):
            if obj.base_type == "soil":
                self.sp = obj
                self._soil_profile_id = obj.id

            elif obj.base_type == "foundation":
                self.fd = obj
                self._foundation_id = obj.id
            elif obj.base_type == "building":
                self.bd = obj
                self._building_id = obj.id

    @property
    def soil_profile_id(self):
        if self._soil_profile_id is None:
            if self._sp.id is not None:
                self._soil_profile_id = self._sp.id
        return self._soil_profile_id

    @property
    def foundation_id(self):
        if self._foundation_id is None:
            if self._fd.id is not None:
                self._foundation_id = self._fd.id
        return self._foundation_id

    @property
    def building_id(self):
        if self._building_id is None:
            if self._bd.id is not None:
                self._building_id = self._bd.id
        return self._building_id

    @property
    def sp(self):
        return self._sp

    @sp.setter
    def sp(self, obj):
        # Could add assertions here for type?
        self._sp = obj
        self._soil_profile_id = obj.id

    @property
    def soil_profile(self):
        return self._sp

    @soil_profile.setter
    def soil_profile(self, obj):
        # Could add assertions here for type?
        self._sp = obj
        self._soil_profile_id = obj.id

    @property
    def fd(self):
        return self._fd

    @fd.setter
    def fd(self, obj):
        # Could add assertions here for type?
        self._fd = obj
        self._foundation_id = obj.id

    @property
    def foundation(self):
        return self._fd

    @foundation.setter
    def foundation(self, obj):
        # Could add assertions here for type?
        self._fd = obj
        self._foundation_id = obj.id

    @property
    def bd(self):
        return self._bd

    @bd.setter
    def bd(self, obj):
        # Could add assertions here for type?
        self._bd = obj
        self._building_id = obj.id

    @property
    def building(self):
        return self._bd

    @building.setter
    def building(self, obj):
        # Could add assertions here for type?
        self._bd = obj
        self._building_id = obj.id

    @property
    def unique_hash(self):
        if self._unique_hash is None:
            self._unique_hash = uuid.uuid1()
        return self._unique_hash


class TwoDSystem(object):
    _unique_hash = None
    base_type = 'system'
    type = 'two_d_system'
    name = None

    def __init__(self, width, height, x_surf=None, y_surf=None, loop=None):
        """
        A two dimensional Soil-structure system

        :param width: float
            Extent of model in x-direction
        :param height:
            Maximum depth of model from datum (y=0)
        :param x_surf: array_like
            x-positions where the surface height is defined in `y_surf`
        :param y_surf: array_like
            y-positions which define the height of the ground surface at each point in the `x_surf` array
        :param loop: float
            Length out-of-plane
        """
        self.width = width
        self.height = height
        if x_surf is None:
            self._x_surf = np.array([0, width])
            self._y_surf = np.array([0, 0])
        else:
            self._x_surf = np.array(x_surf)
            self._y_surf = np.array(y_surf)

        self._sps = []
        self._x_sps = []

        self._bds = []
        self._x_bds = []
        self.inputs = ["base_type", "type", "id", "name", "width", "height", "sps", "x_sps", "bds", "x_bds", "x_surf", "y_surf", "gwl", 'loop']
        self.gwl = 1e6  # can be coordinates
        self.loop = loop

    def to_dict(self, skip_list=None, **kwargs):
        outputs = OrderedDict()
        if skip_list is None:
            skip_list = []
        for item in self.inputs:
            if item not in skip_list:
                value = self.__getattribute__(item)
                if "_id" in item and value is None:
                    raise ModelError("Cannot export system with %s set to None" % item)
                if item not in skip_list:
                    value = self.__getattribute__(item)
                    outputs[item] = sf.collect_serial_value(value)
        return outputs

    def add_to_dict(self, models_dict, **kwargs):
        if self.base_type not in models_dict:
            models_dict[self.base_type] = OrderedDict()
        if "soil_profile" not in models_dict:
            models_dict["soil_profile"] = OrderedDict()
        if "building" not in models_dict:
            models_dict["building"] = OrderedDict()
        if "foundation" not in models_dict:
            models_dict["foundation"] = OrderedDict()
        profile_dict = self.to_dict(skip_list=('x_sps', 'x_bds'), **kwargs)
        profile_dict["sps"] = []
        for i, sp in enumerate(self.sps):
            sp.add_to_dict(models_dict, **kwargs)
            if sp.id is None:
                sp.id = i + 1
            sp.set_soil_ids_to_layers()
            profile_dict["sps"].append({
                "x": self.x_sps[i],
                "soil_profile_id": str(sp.id),
                "soil_profile_unique_hash": str(sp.unique_hash),
            })
        profile_dict["bds"] = []
        for i, bd in enumerate(self.bds):
            if bd.id is None:
                bd.id = i + 1
            if bd.fd is not None:
                if bd.fd.id is None:
                    bd.fd.id = i + 1
                if hasattr(bd.fd, "add_to_dict"):
                    bd.fd.add_to_dict(models_dict, **kwargs)
                else:
                    models_dict["foundation"][bd.fd.unique_hash] = bd.fd.to_dict(**kwargs)
            if hasattr(bd, "add_to_dict"):
                bd.add_to_dict(models_dict, **kwargs)
            else:
                models_dict["building"][bd.unique_hash] = bd.to_dict(**kwargs)
            profile_dict["bds"].append({
                "x": self.x_bds[i],
                "building_id": str(bd.id),
                "building_hash": str(bd.unique_hash),
            })

        models_dict[self.base_type][self.unique_hash] = profile_dict

    def add_sp(self, sp, x):
        self._x_sps.append(float(x))
        self._sps.append(sp)
        inds = np.argsort(self._x_sps)
        self._x_sps = list(np.array(self._x_sps)[inds])
        self._sps = list(np.array(self._sps)[inds])

    def remove_sp(self, x):
        ind = self.x_sps.index(float(x))
        self._x_sps.pop(ind)
        self._sps.pop(ind)

    def remove_sp_by_index(self, ind):
        self._x_sps.pop(ind)
        self._sps.pop(ind)

    @property
    def sps(self):
        return self._sps

    @sps.setter
    def sps(self, sps_w_xs):
        for sp_dict in sps_w_xs:
            x = sp_dict["x"]
            sp = sp_dict["soil_profile"]  # is actually a soil profile object
            self.add_sp(sp, x)

    @property
    def x_sps(self):
        return self._x_sps

    @property
    def bds(self):
        return self._bds

    @bds.setter
    def bds(self, bds_w_xs):
        for bd_dict in bds_w_xs:
            x = bd_dict["x"]
            bd = bd_dict["building"]  # is actually a soil profile object
            self.add_bd(bd, x)

    def add_bd(self, bd, x):
        self._x_bds.append(x)
        self._bds.append(bd)

    @property
    def x_bds(self):
        return self._x_bds

    @property
    def unique_hash(self):
        if self._unique_hash is None:
            self._unique_hash = uuid.uuid1()
        return self._unique_hash

    @property
    def x_surf(self):
        return self._x_surf

    @x_surf.setter
    def x_surf(self, values):
        if values is None:
            self._x_surf = None
        else:
            self._x_surf = np.array(values)

    @property
    def y_surf(self):
        return self._y_surf

    @y_surf.setter
    def y_surf(self, values):
        if values is None:
            self._y_surf = None
        else:
            self._y_surf = np.array(values)

    def get_y_surface_at_x(self, x):
        return np.interp(x, self.x_surf, self.y_surf)

    def get_sp_and_x_sps_for_x(self, x):
        xs = self.x_sps
        inds = np.argsort(xs)
        xs_sorted = np.array(xs)[inds]
        ind = sf.interp_left(x, xs_sorted)
        return self.sps[inds[ind]], xs_sorted[ind]


def trim_system_to_width(tds, target_width, ff_width=30):
    # make last <ff_width> free-field

    x_ff = target_width - ff_width
    y_ff = tds.get_y_surface_at_x(x_ff)
    sp_ref, x_ref = tds.get_sp_and_x_sps_for_x(x_ff)
    # if ff_width is very close to soil profile
    # - then set angles of that sp to zero and move free-field away to avoid meshing issue.
    if x_ff - x_ref < 1:
        sp_ref.x_angles = np.zeros(tds.sps[-1].n_layers)
        sp_ref.x_angles[0] = None
        x_ff = x_ref + 1
    y_ref = tds.get_y_surface_at_x(x_ref)
    lays = np.array(list(sp_ref.layers)[1:]) - np.array(sp_ref.x_angles[1:]) * (x_ff - x_ref) - y_ref + y_ff
    sp_ff = SoilProfile()
    for ll in range(len(lays) + 1):
        if ll == 0:
            sp_ff.add_layer(0, sp_ref.layer(1))
        else:
            sp_ff.add_layer(lays[ll - 1], sp_ref.layer(ll + 1))
    sp_ff.x_angles = np.zeros(len(lays) + 1)
    sp_ff.name = 'free-field'
    sp_ff.height = tds.height + y_ff
    tds.y_surf = np.where(tds.x_surf > x_ff, y_ff, tds.y_surf)
    ind = sf.interp_left(x_ff, tds.x_surf)
    tds.x_surf = np.insert(tds.x_surf, ind + 1, x_ff)
    tds.y_surf = np.insert(tds.y_surf, ind + 1, y_ff)
    rem_xs = []
    for ss in range(len(tds.x_sps)):
        if tds.x_sps[ss] > x_ff:
            rem_xs.append(tds.x_sps[ss])
    rem_xs.sort(reverse=True)
    for xs in rem_xs:
        tds.remove_sp(xs)
    tds.add_sp(sp_ff, x_ff)
    tds.width = target_width


