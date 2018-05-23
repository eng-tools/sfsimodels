__author__ = 'maximmillen'


variable_properties = {}

# generic
variable_properties["name"] = ["Name to identify object", ""]
variable_properties["id"] = ["Id number", ""]

# soil
variable_properties["stype"] = ["Soil model type", ""]
variable_properties["g_mod"] = ["Soil shear modulus", "Pa"]
variable_properties["bulk_mod"] = ["Soil bulk modulus", "Pa"]
variable_properties["poissons_ratio"] = ["Soil Poissons ratio", "Pa"]
variable_properties["phi"] = ["Soil friction angle", "deg"]
variable_properties["cohesion"] = ["Cohesive strength of soil", "Pa"]
variable_properties["dilation_angle"] = ["Soil dilation angle", "deg"]
variable_properties["e_min"] = ["Minimum void ratio", ""]
variable_properties["e_max"] = ["Maximum void ratio", ""]
variable_properties["e_curr"] = ["Current void ratio", ""]
variable_properties["relative_density"] = ["Relative density", ""]
variable_properties["specific_gravity"] = ["Specific gravity of soil", ""]
variable_properties["unit_dry_weight"] = ["Dry unit weight of soil", "N/m3"]
variable_properties["unit_sat_weight"] = ["Saturated unit weight of soil", "N/m3"]
variable_properties["saturation"] = ["Saturation ratio of soil", ""]
variable_properties["permeability"] = ["Permeability of soil", ""]

variable_properties["e_cr0"] = ["", ""]
variable_properties["p_cr0"] = ["", ""]
variable_properties["lamb_crl"] = ["", ""]

# soil profile
variable_properties["gwl"] = ["Ground water level", "m"]
variable_properties["unit_water_weight"] = ["Unit weight of water", "N/m3"]
variable_properties["height"] = ["Total height of soil profile", "m"]
variable_properties["layers"] = ["Layers of soil specified by depth to top of layer", "m"]

# foundation
variable_properties["ftype"] = ["Foundation type", ""]
variable_properties["width"] = ["Foundation width", "m"]
variable_properties["length"] = ["Foundation length", "m"]
variable_properties["depth"] = ["Foundation depth", "m"]
variable_properties["mass"] = ["Foundation mass", "kg"]
variable_properties["density"] = ["Foundation mass density", "kg/m3"]

# pad foundation
variable_properties["n_pads_l"] = ["Number of footings in length direction", ""]
variable_properties["n_pads_w"] = ["Number of footings in width direction", "kg/m3"]
variable_properties["pad_length"] = ["Length of footing", "m"]
variable_properties["pad_width"] = ["Width of footing", "m"]

# structure
variable_properties["h_eff"] = ["Structure effective height", "m"]
variable_properties["mass_eff"] = ["Structure effective mass", "T"]
variable_properties["t_fixed"] = ["Structure effective period", "s"]
variable_properties["mass_ratio"] = ["Ratio of horizontal seismic mass to vertical mass", ""]

# hazard
variable_properties["z_factor"] = ["Hazard factor (Z)", ""]
variable_properties["r_factor"] = ["Return period factor (R)", ""]
variable_properties["n_factor"] = ["Near-field factor (N)", ""]
variable_properties["magnitude"] = ["Magnitude", ""]
variable_properties["corner_period"] = ["Spectrum corner period", "s"]
variable_properties["corner_acc_factor"] = ["Spectrum corner acceleration factor", ""]