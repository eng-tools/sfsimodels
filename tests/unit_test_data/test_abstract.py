from sfsimodels import CustomObject
from sfsimodels import Foundation


class SimpleObject(object):
    inputs = ["name",
              "arm"]
    name = "simple"
    arm = 4


def test_abstract_add_from_same():
    custom_obj = CustomObject()
    custom_obj.name = "custom"
    simple_obj = SimpleObject()
    custom_obj.add_from_same(simple_obj, inputs_from="obj", update_inputs=True)
    assert custom_obj.name == "simple"
    assert custom_obj.arm == 4
    assert "name" in custom_obj.inputs

    custom_obj = CustomObject()
    custom_obj.name = "custom"
    simple_obj = SimpleObject()
    custom_obj.add_from_same(simple_obj, inputs_from="obj", update_inputs=False)
    assert custom_obj.name == "simple"
    assert custom_obj.arm == 4
    assert "arm" not in custom_obj.inputs

    custom_obj = CustomObject()
    custom_obj.name = "custom"
    simple_obj = SimpleObject()
    custom_obj.add_from_same(simple_obj, inputs_from="self")
    assert custom_obj.name == "simple"
    assert not hasattr(custom_obj, "arm")
    assert "arm" not in custom_obj.inputs


if __name__ == '__main__':
    test_abstract_add_from_same()