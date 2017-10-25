__author__ = 'maximmillen'


variable_properties = {}
# soil
variable_properties["G_mod"] = ["Soil shear modulus", "Mpa"]
variable_properties["phi"] = ["Soil friction angle", "deg"]
variable_properties["relative_density"] = ["Relative density", ""]
variable_properties["height_crust"] = ["Crust height", "m"]
variable_properties["height_liq"] = ["Liquefied layer height", "m"]
variable_properties["gwl"] = ["Ground water level", "m"]
variable_properties["unit_weight_crust"] = ["Unit weight of crust", "kN/m3"]
variable_properties["unit_sat_weight_liq"] = ["Unit weight of liq. layer", "kN/m3"]
variable_properties["unit_weight_water"] = ["Unit weight of water", "kN/m3"]
variable_properties["cohesion"] = ["Cohesion", "kPa"]
variable_properties["piossons_ratio"] = ["Piosson's ratio", ""]
variable_properties["e_min"] = ["Minimum void ratio", ""]
variable_properties["e_max"] = ["Maximum void ratio", ""]
variable_properties["e_cr0"] = ["", ""]
variable_properties["p_cr0"] = ["", ""]
variable_properties["lamb_crl"] = ["", ""]
# foundation
variable_properties["width"] = ["Foundation width", "m"]
variable_properties["length"] = ["Foundation length", "m"]
variable_properties["depth"] = ["Foundation depth", "m"]
# structure
variable_properties["h_eff"] = ["Structure effective height", "m"]
variable_properties["mass_eff"] = ["Structure effective mass", "T"]
variable_properties["t_eff"] = ["Structure effective period", "s"]
variable_properties["mass_ratio"] = ["Seismic mass ratio", ""]
# hazard
variable_properties["z_factor"] = ["Hazard factor (Z)", ""]
variable_properties["r_factor"] = ["Return period factor (R)", ""]
variable_properties["n_factor"] = ["Near-field factor (N)", ""]
variable_properties["magnitude"] = ["Magnitude", ""]
variable_properties["corner_period"] = ["Spectrum corner period", "s"]
variable_properties["corner_acc_factor"] = ["Spectrum corner acceleration factor", ""]