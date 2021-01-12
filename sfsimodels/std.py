import sfsimodels as sm


def create_rc_beam(depth=None, width=None, n_sects=1):
    rc_sect = sm.sections.RCBeamSection
    rc_mat = sm.materials.ReinforcedConcreteMaterial()
    ele = sm.BeamColumnElement(n_sects=n_sects, section_class=rc_sect)
    if depth is not None:
        ele.set_section_prop('depth', depth)
    if width is not None:
        ele.set_section_prop('width', width)
    ele.set_section_prop('mat', rc_mat)
    return ele
