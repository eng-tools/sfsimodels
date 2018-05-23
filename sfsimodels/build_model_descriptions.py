from sfsimodels import models
from sfsimodels import properties

vp = properties.variable_properties


def add_items(obj, para):
    para.append(obj.__class__.__name__ + " inputs:")
    for item in obj.inputs:

        if item in vp:
            para.append(",".join([item, vp[item][0], vp[item][1]]))
        else:
            para.append(item)


def descriptions():
    """
    Generates a list of descriptions of all the models

    :return:
    """
    para = []
    add_items(models.Soil(), para)
    add_items(models.SoilProfile(), para)
    add_items(models.Foundation(), para)
    add_items(models.PadFoundation(), para)
    add_items(models.Structure(), para)

    print("\n".join(para))