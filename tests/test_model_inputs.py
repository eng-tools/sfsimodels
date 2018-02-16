
from sfsimodels import models as dm

def test_model_inputs():
    p_models = [dm.SeismicHazard(),
                dm.FrameBuilding(),
                dm.WallBuilding(),
                dm.Soil(),
                dm.material.Concrete()]
    for model in p_models:
        for parameter in model.inputs:
            assert hasattr(model, parameter), parameter
