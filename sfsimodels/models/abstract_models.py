import copy
from sfsimodels.loader import add_inputs_to_object
import types

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
        add_inputs_to_object(self, values)

    def deepcopy(self):
        """ Make a clone of the object """
        return copy.deepcopy(self)

    @property
    def base_types(self):
        return ["physical_object"]
