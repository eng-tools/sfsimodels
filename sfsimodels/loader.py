__author__ = 'maximmillen'

import numpy as np
from sfsimodels import models


def add_inputs_to_object(obj, values):
    """
    A generic function to load object parameters based on a dictionary list.

    Parameters
    ----------
    obj: object
    values: dict
    """
    for item in obj.inputs:
        if hasattr(obj, item):
            # print(item)
            setattr(obj, item, values[item])


def load_sample_data(sss):
    """
    Adds sample data to a SoilStructureSystem object

    Parameters
    ----------
    sss: SoilStructureSystem
    """

    load_soil_sample_data(sss.sp)  # soil
    load_foundation_sample_data(sss.fd)  # foundation
    load_structure_sample_data(sss.bd)  # structure
    load_hazard_sample_data(sss.hz)  # hazard


def load_soil_sample_data(sp):
    """
    Adds sample data to a Soil object

    Parameters
    ----------
    sp: Soil Object
    """
    # soil
    sp.g_mod = 60.0e6  # [Pa]
    sp.phi = 30  # [degrees]
    sp.relative_density = .40  # [decimal]
    sp.gwl = 2.  # [m], ground water level
    sp.unit_dry_weight = 17000  # [N/m3]
    sp.unit_sat_weight = 18000  # [N/m3]
    sp.unit_weight_water = 9800  # [N/m3]
    sp.cohesion = 10.0  # [Pa]
    sp.poissons_ratio = 0.22
    sp.e_min = 0.55
    sp.e_max = 0.95
    sp.e_critical0 = 0.79  # Jin et al. 2015
    sp.p_critical0 = 0.7  # Jin et al. 2015
    sp.lamb_crl = 0.015  # Jin et al. 2015


def load_foundation_sample_data(fd):
    """
    Adds sample data to a Foundation object

    Parameters
    ----------
    fd: Foundation Object
    :return:
    """
    # foundation
    fd.width = 16.0  # m
    fd.length = 18.0  # m
    fd.depth = 0.0  # m
    fd.mass = 0.0


def load_structure_sample_data(st):
    """
    Adds sample data to a Structure object

    Parameters
    ----------
    st: Structure Object
    """
    # structure
    st.h_eff = 9.0  # m
    st.mass_eff = 120e3  # kg
    st.t_eff = 1.0  # s
    st.mass_ratio = 1.0  # ratio of mass acting horizontal to vertically


def load_hazard_sample_data(hz):
    """
    Sample data for the Hazard object

    Parameters
    ----------
    hz: Hazard Object
    """
    # hazard
    hz.z_factor = 0.3  # Hazard factor
    hz.r_factor = 1.0  # Return period factor
    hz.n_factor = 1.0  # Near-fault factor
    hz.magnitude = 7.5  # Magnitude of earthquake
    hz.corner_period = 4.0  # s
    hz.corner_acc_factor = 0.55
    return hz


def load_building_sample_data(bd):
    """
    Sample data for the Building object

    Parameters
    ----------
    bd:
    """
    number_of_storeys = 6
    interstorey_height = 3.4  # m
    masses = 40.0e3  # kg

    bd.interstorey_heights = interstorey_height * np.ones(number_of_storeys)
    bd.floor_length = 18.0  # m
    bd.floor_width = 16.0  # m
    bd.storey_masses = masses * np.ones(number_of_storeys)  # kg


def load_frame_building_sample_data():
    """
    Sample data for the BuildingFrame object
    """
    number_of_storeys = 6
    interstorey_height = 3.4  # m
    masses = 40.0e3  # kg
    n_bays = 3

    fb = models.FrameBuilding(number_of_storeys, n_bays)
    fb.interstorey_heights = interstorey_height * np.ones(number_of_storeys)
    fb.floor_length = 18.0  # m
    fb.floor_width = 16.0  # m
    fb.storey_masses = masses * np.ones(number_of_storeys)  # kg

    fb.bay_lengths = [6., 6.0, 6.0]
    fb.set_beam_prop("depth", [0.5, 0.5, 0.5], repeat="up")
    fb.set_beam_prop("width", [0.4, 0.4, 0.4], repeat="up")
    fb.set_column_prop("width", [0.5, 0.5, 0.5, 0.5], repeat="up")
    fb.set_column_prop("depth", [0.5, 0.5, 0.5, 0.5], repeat="up")
    fb.n_seismic_frames = 3
    fb.n_gravity_frames = 0
    return fb


