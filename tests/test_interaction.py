from sfsimodels import models
import sfsimodels as sm
import json
import numpy as np


def test_link_building_and_soil():
    number_of_storeys = 6
    interstorey_height = 3.4  # m
    n_bays = 3

    fb = models.FrameBuilding(number_of_storeys, n_bays)
    fb.id = 1
    fb.interstorey_heights = interstorey_height * np.ones(number_of_storeys)
    fb.floor_length = 18.0  # m
    fb.floor_width = 16.0  # m

    fd = models.RaftFoundation()
    fd.length = 4
    fd.width = 6
    fd.height = 0.0
    fd.density = 3

    fd2 = models.RaftFoundation()
    fd2.length = 14
    fd2.width = 16
    fd2.height = 10.0
    fd2.density = 13

    # link building to foundation
    fd.set_building(fb, two_way=False)
    assert fd.building.n_bays == 3
    assert fb.foundation is None
    fd.set_building(fb, two_way=True)
    assert fb.foundation.length == 4

    # one way link
    fb.set_foundation(fd2, two_way=False)
    assert fb.foundation.length == 14
    assert fd2.building is None
    fb.set_foundation(fd2, two_way=True)
    assert fb.foundation.length == 14
    assert np.isclose(fd2.building.floor_width, 16.0)

    structure = models.SDOFBuilding()
    structure.set_foundation(fd, two_way=True)
    assert structure.foundation.width == 6
    assert isinstance(fd.building, models.SDOFBuilding)


def test_save_and_load_w_linked_building_and_soil():
    number_of_storeys = 6
    interstorey_height = 3.4  # m

    wb = models.WallBuilding(number_of_storeys)
    wb.id = 1
    wb.interstorey_heights = interstorey_height * np.ones(number_of_storeys)
    wb.floor_length = 18.0  # m
    wb.floor_width = 16.0  # m

    fd = models.RaftFoundation()
    fd.length = 4
    fd.width = 6
    fd.height = 0.0
    fd.density = 3
    fd.id = 1

    # link building to foundation
    fd.set_building(wb, two_way=False)
    assert fd.building.n_storeys == number_of_storeys
    assert wb.foundation is None
    fd.set_building(wb, two_way=True)
    assert wb.foundation.length == 4
    print(wb.foundation_id)

    ecp_output = sm.Output()
    ecp_output.add_to_dict(wb)
    ecp_output.add_to_dict(fd)

    ecp_output.name = "a single wall building"
    ecp_output.units = "N, kg, m, s"
    ecp_output.comments = ""
    p_str = json.dumps(ecp_output.to_dict(), skipkeys=["__repr__"], indent=4)
    print(p_str)
    objs = sm.loads_json(p_str)
    building = objs["building"][1]
    foundation = objs["foundation"][1]
    print(building.foundation.length)
    assert np.isclose(building.floor_length, 18.0)


if __name__ == '__main__':
    test_save_and_load_w_linked_building_and_soil()