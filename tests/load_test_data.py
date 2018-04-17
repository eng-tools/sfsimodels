__author__ = 'maximmillen'

import numpy as np


def add_inputs_to_object(obj, values):
    """
    A generic function to load object parameters based on a dictionary list.
    :param obj: Object
    :param values: Dictionary
    :return:
    """
    for item in obj.inputs:
        if hasattr(obj, item):
            # print(item)
            setattr(obj, item, values[item])

def load_soil_test_data(sl):
    """
    Sample data for the Soil object
    :param sl: Soil Object
    :return:
    """
    # soil
    sl.id = 1
    sl.g_mod = 60.0e6  # [Pa]
    sl.phi = 30  # [degrees]
    sl.relative_density = .40  # [decimal]
    sl.gwl = 2.  # [m], ground water level
    sl.unit_dry_weight = 17000  # [N/m3]
    sl.unit_moist_weight = 18000  # [N/m3]
    sl.unit_weight_water = 9800  # [N/m3]
    sl.cohesion = 10.0  # [Pa]
    sl.poissons_ratio = 0.22
    sl.e_min = 0.55
    sl.e_max = 0.95
    sl.e_critical0 = 0.79  # Jin et al. 2015
    sl.p_critical0 = 0.7  # Jin et al. 2015
    sl.lamb_crl = 0.015  # Jin et al. 2015
    

def load_soil_profile_test_data(sp):
    sp.id = "1"
    sl = sp.layer(1)
    load_soil_test_data(sl)
    


def load_foundation_test_data(fd):
    """
    Sample data for the Foundation object
    :param fd: Foundation Object
    :return:
    """
    # foundation
    fd.id = "1"
    fd.width = 16.0  # m
    fd.length = 18.0  # m
    fd.depth = 0.0  # m
    fd.mass = 0.0


def load_structure_test_data(st):
    """
    Sample data for the Structure object
    :param st: Structure Object
    :return:
    """
    # structure
    st.id = "1"
    st.h_eff = 9.0  # m
    st.mass_eff = 120e3  # kg
    st.t_eff = 1.0  # s
    st.mass_ratio = 1.0  # ratio of mass acting horizontal to vertically


def load_hazard_test_data(hz):
    """
    Sample data for the Hazard object
    :param hz: Hazard Object
    :return:
    """
    # hazard
    hz.id = "1"
    hz.z_factor = 0.3  # Hazard factor
    hz.r_factor = 1.0  # Return period factor
    hz.n_factor = 1.0  # Near-fault factor
    hz.magnitude = 7.5  # Magnitude of earthquake
    hz.corner_period = 4.0  # s
    hz.corner_acc_factor = 0.55
    return hz


def load_building_test_data(bd):
    """
    Sample data for the Building object
    :param bd:
    :return:
    """
    number_of_storeys = 6
    interstorey_height = 3.4  # m
    masses = 40.0e3  # kg
    bd.id = 1
    bd.interstorey_heights = interstorey_height * np.ones(number_of_storeys)
    bd.floor_length = 18.0  # m
    bd.floor_width = 16.0  # m
    bd.storey_masses = masses * np.ones(number_of_storeys)  # kg


def load_frame_building_test_data(fb):
    """
    Sample data for the FrameBuilding object
    :param fb:
    :return:
    """
    load_building_test_data(fb)

    fb.bay_lengths = [6., 6.0, 6.0]
    fb.beam_depths = [.5]
    fb.n_seismic_frames = 3
    fb.n_gravity_frames = 0


def load_test_data(sss):
    """
    Sample data for the SoilStructureSystem object
    :param sss:
    :return:
    """
    sss.id = 1
    load_soil_profile_test_data(sss.sp)  # soil_profile
    load_foundation_test_data(sss.fd)  # foundation
    load_structure_test_data(sss.bd)  # structure
    # load_hazard_test_data(sss.hz)  # hazard

