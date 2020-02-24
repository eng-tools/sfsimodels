pp = {}  # TODO: switch to read description from docstring, or extend the string object

# generic
pp["physical_object"] = {}
pp["physical_object"]["type"] = ["Object type", ""]
pp["physical_object"]["base_type"] = ["Object type for saving and loading", ""]
pp["physical_object"]["name"] = ["Name to identify object", ""]
pp["physical_object"]["id"] = ["Id number", ""]

# soil
pp["soil"] = {}
pp["soil"]["stype"] = ["Soil model type", ""]
pp["soil"]["g_mod"] = ["Soil shear modulus", "Pa"]
pp["soil"]["bulk_mod"] = ["Soil bulk modulus", "Pa"]
pp["soil"]["poissons_ratio"] = ["Soil Poissons ratio", "Pa"]
pp["soil"]["phi"] = ["Soil friction angle", "deg"]
pp["soil"]["cohesion"] = ["Cohesive strength of soil", "Pa"]
pp["soil"]["dilation_angle"] = ["Soil dilation angle", "deg"]
pp["soil"]["e_min"] = ["Minimum void ratio", "-"]
pp["soil"]["e_max"] = ["Maximum void ratio", "-"]
pp["soil"]["e_curr"] = ["Current void ratio", "-"]
pp["soil"]["relative_density"] = ["Relative density", "-"]
pp["soil"]["specific_gravity"] = ["Specific gravity of soil", "-"]
pp["soil"]["unit_dry_weight"] = ["Dry unit weight of soil", "N/m3"]
pp["soil"]["unit_sat_weight"] = ["Saturated unit weight of soil", "N/m3"]
pp["soil"]["saturation"] = ["Saturation ratio of soil", "-"]
pp["soil"]["plasticity_index"] = ["Plasticity index of the soil", "-"]
pp["soil"]["permeability"] = ["Permeability of soil", "-"]

pp["soil_critical"] = {}
pp["soil_critical"]["e_cr0"] = ["", ""]
pp["soil_critical"]["p_cr0"] = ["", ""]
pp["soil_critical"]["lamb_crl"] = ["", ""]

# soil profile
pp["soil_profile"] = {}
pp["soil_profile"]["gwl"] = ["Ground water level", "m"]
pp["soil_profile"]["unit_water_weight"] = ["Unit weight of water", "N/m3"]
pp["soil_profile"]["height"] = ["Total height of soil profile", "m"]
pp["soil_profile"]["layers"] = ["Layers of soil specified by id and depth to top of layer", "m"]

# foundation
pp["foundation"] = {}
pp["foundation"]["ftype"] = ["Foundation type", ""]
pp["foundation"]["width"] = ["Foundation width", "m"]
pp["foundation"]["length"] = ["Foundation length", "m"]
pp["foundation"]["depth"] = ["Foundation depth from surface", "m"]
pp["foundation"]["height"] = ["Foundation height", "m"]
pp["foundation"]["mass"] = ["Foundation mass", "kg"]
pp["foundation"]["density"] = ["Foundation mass density", "kg/m3"]

# pad foundation
pp["pad_foundation"] = {}
pp["pad_foundation"]["n_pads_l"] = ["Number of footings in length direction", ""]
pp["pad_foundation"]["n_pads_w"] = ["Number of footings in width direction", ""]
pp["pad_foundation"]["pad_length"] = ["Length of footing", "m"]
pp["pad_foundation"]["pad_width"] = ["Width of footing", "m"]

# structure
pp["structure"] = {}
pp["structure"]["h_eff"] = ["Structure effective height", "m"]
pp["structure"]["mass_eff"] = ["Structure effective mass", "T"]
pp["structure"]["t_fixed"] = ["Structure effective period", "s"]
pp["structure"]["mass_ratio"] = ["Ratio of horizontal seismic mass to vertical mass", ""]

pp["building"] = {}
pp["building"]["floor_length"] = ["Length of floor area in direction of interest", "m"]
pp["building"]["floor_width"] = ["Length of floor area out-of-plane", "m"]
pp["building"]["interstorey_heights"] = ["Distance between storeys", "m"]
pp["building"]["storey_masses"] = ["Mass of each storey", "kg"]

pp["frame_building_2D"] = {}
pp["frame_building_2D"]["beams"] = ["Array of beam sections", "m"]
pp["frame_building_2D"]["columns"] = ["Array of column sections", "m"]
pp["frame_building_2D"]["bay_lengths"] = ["Length between columns", "m"]
pp["frame_building_2D"]["beam_depths"] = ["Depth of beams", "m"]
# pp["frame_building"]["n_seismic_frames"] = ["Number of seismic frames", ""]
# pp["frame_building"]["n_gravity_frames"] = ["Number of gravity frames", ""]

# hazard
pp["seismic_hazard"] = {}
pp["seismic_hazard"]["z_factor"] = ["Hazard factor (Z)", ""]
pp["seismic_hazard"]["r_factor"] = ["Return period factor (R)", ""]
pp["seismic_hazard"]["n_factor"] = ["Near-field factor (N)", ""]
pp["seismic_hazard"]["magnitude"] = ["Magnitude", ""]
pp["seismic_hazard"]["corner_period"] = ["Spectrum corner period", "s"]
pp["seismic_hazard"]["corner_acc_factor"] = ["Spectrum corner acceleration factor", ""]