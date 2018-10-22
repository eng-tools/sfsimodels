
from sfsimodels import models as dm


def test_model_inputs():
    p_models = [dm.SeismicHazard(),
                dm.BuildingFrame(1, 2),
                dm.BuildingWall(1),
                dm.Soil(),
                dm.material.Concrete()]
    for model in p_models:
        for parameter in model.inputs:
            assert hasattr(model, parameter), parameter
