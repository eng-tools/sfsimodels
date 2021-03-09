from collections import OrderedDict
import copy
# from sfsimodels.loader import add_inputs_to_object
import types
from sfsimodels.exceptions import ModelError
from sfsimodels.models.units import Units
from sfsimodels.models.coordinates import Coords
from sfsimodels import functions as sf
import uuid
import hashlib
import json
json.encoder.FLOAT_REPR = lambda f: ("%.5g" % f)


class PhysicalObject(object):
    _id = None
    name = None
    _counter = 0
    type = "physical_object"
    _unique_hash = None
    _loaded_unique_hash = None  # This is only set when the model is loaded from an ecp file
    # inputs = ()
    _tolerance = 0.0001  # consistency tolerance
    skip_list = ()
    _units = None
    # _coords = None

    def __iter__(self):  # real signature unknown
        return self

    # def __init__(self, **kwargs):
    #     # super(PhysicalObject, self).__init__()
    #     print("Initialised")

    @property
    def attributes(self):
        all_attributes = []
        for item in self.__dir__():
            if item in ["deepcopy", "set", "to_dict"]:
                continue
            if isinstance(item, types.MethodType):
                continue
            if "_" != item[0]:
                all_attributes.append(item)
        all_attributes.sort()
        return all_attributes

    def __next__(self):
        self._counter += 1
        all_attributes = self.attributes
        if self._counter == len(all_attributes):
            raise StopIteration
        return all_attributes[self._counter]

    def set(self, values):
        """
        Set the object parameters using a dictionary
        """
        if hasattr(self, "inputs"):
            for item in self.inputs:
                if hasattr(self, item):
                    setattr(self, item, values[item])

    def deepcopy(self):
        """ Make a clone of the object """
        obj = copy.deepcopy(self)
        obj.clear_unique_hash()
        return obj

    @property
    def ancestor_types(self):
        return ["physical_object"]

    def add_from_same(self, obj, inputs_from="obj", update_inputs=True):
        if not hasattr(self, "inputs"):
            raise ModelError("self does not contain attribute: 'inputs'")
        if inputs_from == "obj":
            if hasattr(obj, "inputs"):
                inputs_list = obj.inputs
            else:
                raise ModelError("obj does not contain attribute: 'inputs'")
        else:
            inputs_list = self.inputs
        for item in inputs_list:
            if hasattr(obj, item):
                try:
                    setattr(self, item, getattr(obj, item))
                except ModelError:
                    continue
                if update_inputs and item not in self.inputs:
                    self.inputs.append(item)

    def to_dict(self, extra=(), **kwargs):
        outputs = OrderedDict()
        export_none = kwargs.get("export_none", True)
        if hasattr(self, "inputs"):
            full_inputs = list(self.inputs) + list(extra)
        else:
            full_inputs = list(extra)
        for item in full_inputs:
            if item not in self.skip_list:
                # if item.endswith('_id'):
                #     obj =
                value = self.__getattribute__(item)
                if not export_none and value is None:
                    continue
                outputs[item] = sf.collect_serial_value(value, export_none=export_none)
        with_hash = kwargs.get('with_hash', True)
        if with_hash:
            outputs['unique_hash'] = self.unique_hash
        return outputs

    @property
    def unique_hash(self):
        if self._unique_hash is None:
            # self._unique_hash = uuid.uuid1()
            self._unique_hash = hashlib.md5(json.dumps(self.to_dict(with_hash=False)).encode('utf-8')).hexdigest()
        return self._unique_hash

    def clear_unique_hash(self):
        self._unique_hash = None

    def recompute_unique_hash(self):
        self._unique_hash = hashlib.md5(json.dumps(self.to_dict(with_hash=False)).encode('utf-8')).hexdigest()
        return self._unique_hash

    @property
    def loaded_unique_hash(self):
        return self._loaded_unique_hash

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        if value not in [None, ""]:
            self._id = int(value)

    @property
    def units(self):
        return self._units

    @units.setter
    def units(self, units_obj):
        assert isinstance(units_obj, Units)
        self._units = units_obj

    # @property
    # def coords(self):
    #     return self._coords
    #
    # @coords.setter
    # def coords(self, coords_obj):
    #     assert isinstance(coords_obj, Coords)
    #     self._coords = coords_obj


class CustomObject(PhysicalObject):
    """
    An object to describe structures.
    """
    base_type = "custom_object"
    type = "custom_object"

    def __init__(self):
        self.inputs = [
            "id",
            "name",
            "base_type",
            "type",
            "units"
            ]

    @property
    def ancestor_types(self):
        return ["custom"]
