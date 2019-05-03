import sfsimodels as sm

sl = sm.Soil()
sl.specific_gravity = 2.65
sl.e_curr = 0.6

print(sl.unit_dry_weight)
sl2 = sm.Soil()
sl2.specific_gravity = 2.65
sl2.e_curr = 0.6


sp = sm.SoilProfile()
sp.add_layer(0.0, sl)
sp.add_layer(5.0, sl2)
sp.gwl = 2.0

print(sp.get_v_eff_stress_at_depth(3))
