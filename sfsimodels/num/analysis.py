import numpy as np


class AnalysisPhase(object):
    atype = None
    dt = None
    dof = None
    values = None
    times = None
    loc = None  # str to indicate which node
    bsteps = 20  # block steps
    dt_fmax = 10
    dt_fmin = 0.05
    on_fail = 'raise'  # break
    ifrc = 0  # interface is frictional

    def __init__(self, dof, values, times, dt, on_fail='raise'):
        self.dof = dof
        self.values = np.array(values)
        self.times = np.array(times)
        self.dt = dt
        self.on_fail = on_fail


class LoadPhase(AnalysisPhase):
    atype = 'load'


class DispPhase(AnalysisPhase):
    atype = 'disp'


class FreePhase(AnalysisPhase):
    atype = 'free'


class DynamicPhase(AnalysisPhase):
    atype = 'dynamic'
    dt = None
    dof = None
    btype = None  # fixed or free

    def __init__(self, dof, values, times, dt, on_fail='raise', btype='fixed'):
        self.dof = dof
        self.values = np.array(values)
        self.times = np.array(times)
        self.dt = dt
        self.on_fail = on_fail
        self.btype = btype
