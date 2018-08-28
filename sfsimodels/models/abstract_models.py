from collections import OrderedDict
import copy
# from sfsimodels.loader import add_inputs_to_object
import types
from sfsimodels.exceptions import ModelError


class PhysicalObject(object):
    _counter = 0
    type = "physical_object"

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
        return copy.deepcopy(self)

    @property
    def ancestor_types(self):
        return ["physical_object"]


class CustomObject(PhysicalObject):
    """
    An object to describe structures.
    """
    _id = None
    name = None
    base_type = "custom_object"
    type = "custom_object"

    def __init__(self):
        self.inputs = [
            "id",
            "name",
            "base_type",
            "type"
            ]

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
        return ["custom"]

    def add_from_same(self, obj, inputs_from="obj", update_inputs=True):
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


