from collections import OrderedDict
import copy
# from sfsimodels.loader import add_inputs_to_object
import types
from sfsimodels.exceptions import ModelError
from sfsimodels import functions as sf
import uuid
import hashlib
import json
json.encoder.FLOAT_REPR = lambda f: ("%.5g" % f)


class BaseECPModel(object):
    _id = None
    name = None
    _counter = 0
    _unique_hash = None

    _tolerance = 0.0001  # consistency tolerance
    skip_list = ()
    #
    # def __iter__(self):  # real signature unknown
    #     return self
    #
    #

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

    # def __next__(self):
    #     self._counter += 1
    #     all_attributes = self.attributes
    #     if self._counter == len(all_attributes):
    #         raise StopIteration
    #     return all_attributes[self._counter]

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
        return copy.deepcopy(self)

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
                setattr(self, item, getattr(obj, item))
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
                value = self.__getattribute__(item)
                if not export_none and value is None:
                    continue
                outputs[item] = sf.collect_serial_value(value)
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
