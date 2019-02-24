import sfsimodels as sm


def test_set_soil_prop():
    sl = sm.Soil(e_min=0.4)
    assert sl.e_min == 0.4


# class ExtSoil(sm.Soil):
#     def __init__(self, pw=9800, **kwargs):
#         super(ExtSoil, self).__init__(pw=pw)  # run parent class initialiser function
#         self._extra_class_inputs = []
#         self.inputs = self.inputs + self._extra_class_inputs
#         for param in kwargs:
#             if param in self.inputs:
#                 setattr(self, param, kwargs[param])
#
#     def e_min(self, val):
#         return val
#
#
# def test_set_extended_soil_prop():
#     sl = ExtSoil(e_min=0.4)
#     print(sl.e_min(0.3))


def test_set_crit_soil_prop():
    sl = sm.CriticalSoil(e_min=0.4, p_cr0=0.5)
    assert sl.e_min == 0.4
    assert sl.p_cr0 == 0.5
