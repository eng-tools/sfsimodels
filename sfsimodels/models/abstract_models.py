import copy
from sfsimodels.loader import add_inputs_to_object


class PhysicalObject(object):
    _counter = 0

    def __iter__(self):  # real signature unknown
        return self

    @property
    def attributes(self):
        all_attributes = []
        for item in self.__dir__():
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
        """""
        Set the frame object parameters using a dictionary
        """""
        add_inputs_to_object(self, values)

    def deepcopy(self):
        """ Make a clone of the object """
        return copy.deepcopy(self)