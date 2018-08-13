from sfsimodels import models
from sfsimodels import properties
from sfsimodels import exceptions

vp = properties.pp


def build_parameter_descriptions(obj, user_p={}, show_none=True, ignore_list=[]):
    """
    Creates a list of the decription of all the inputs of an object

    :param obj: object, that has parameters
    :param user_p: dict, user defined parameter descriptions
    :param show_none: if false, only shows descriptions of parameters that are not None
    :return:
    """
    para = [obj.__class__.__name__ + " inputs:,,"]
    if not hasattr(obj, 'inputs'):
        raise exceptions.ModelError("Object must contain parameter 'inputs'")

    p_dict = {}
    if hasattr(obj, 'ancestor_types'):
        bt = obj.ancestor_types
        for otype in bt:  # cycles from lowest class, so descriptions get overridden
            if otype in vp:
                for item in vp[otype]:
                    p_dict[item] = vp[otype][item]
        for item in user_p:  # user defined definitions override base ones
            p_dict[item] = user_p[item]
    else:
        p_dict = user_p

    for item in obj.inputs:
        if show_none is False and getattr(obj, item) is None:
            continue
        if item in ignore_list:
            continue
        if item in p_dict:
            para.append(",".join([item, p_dict[item][1], p_dict[item][0]]))
        else:
            para.append(item)
    return para


def all_descriptions():
    """
    Generates a list of descriptions of all the models

    :return:
    """
    para = []
    para += build_parameter_descriptions(models.Soil()) + [",,\n"]
    para += build_parameter_descriptions(models.SoilProfile()) + [",,\n"]
    para += build_parameter_descriptions(models.Foundation()) + [",,\n"]
    para += build_parameter_descriptions(models.PadFoundation()) + [",,\n"]
    para += build_parameter_descriptions(models.Structure()) + [",,\n"]
    para += build_parameter_descriptions(models.FrameBuilding2D(1, 1))

    return para


if __name__ == '__main__':
    # all_descriptions()
    para = []
    para += build_parameter_descriptions(models.Soil()) + [",,\n"]
    para += build_parameter_descriptions(models.SoilProfile()) + [",,\n"]
    para += build_parameter_descriptions(models.Foundation()) + [",,\n"]
    para += build_parameter_descriptions(models.PadFoundation()) + [",,\n"]
    para += build_parameter_descriptions(models.Structure()) + [",,\n"]
    para += build_parameter_descriptions(models.FrameBuilding2D(1, 1))
    print("\n".join(para))
