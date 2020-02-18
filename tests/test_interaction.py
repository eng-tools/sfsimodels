from sfsimodels import models
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
