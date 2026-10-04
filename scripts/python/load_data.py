"""Helpers to read the extracted scope data (data/fig_data/*.mat) and logged signals (data/sim/*.mat)."""
import os
import numpy as np
import scipy.io as sio

ROOT = os.environ.get('CMRCC_ROOT', os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
FIG_DATA = os.path.join(ROOT, 'data', 'fig_data')
SIM_DATA = os.path.join(ROOT, 'data', 'sim')

_cache, _sim = {}, {}


def sig(fig, name=None):
    """Return (t, y) for a trace of a scope figure; name=None takes the only/first trace."""
    if fig not in _cache:
        S = np.atleast_1d(sio.loadmat(os.path.join(FIG_DATA, fig + '.mat'), squeeze_me=True,
                                      struct_as_record=False)['S'])
        _cache[fig] = {s.name: s for s in S}
    d = _cache[fig]
    s = d[name] if name else list(d.values())[0]
    t = s.t0 + s.dt * np.arange(s.n)
    return t, np.asarray(s.y, dtype=float)


def simsig(model, k):
    """Return (t, y) for a signal logged by scripts/matlab/log_extra_signals.m."""
    if model not in _sim:
        _sim[model] = sio.loadmat(os.path.join(SIM_DATA, model + '_sim.mat'), squeeze_me=True,
                                  struct_as_record=False)['R']
    s = getattr(_sim[model], k)
    return np.asarray(s.t, float), np.asarray(s.y, float)


def win(t, y, a, b):
    m = (t >= a) & (t <= b)
    return t[m], y[m]
