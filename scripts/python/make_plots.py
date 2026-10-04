"""Re-create the result figures (300 dpi) from the extracted scope data and logged signals."""
import numpy as np, sys, os, json, scipy.io as sio
from load_data import sig, win, simsig, ROOT
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = os.path.join(ROOT, 'figures', 'results') + os.sep
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman'], 'mathtext.fontset': 'stix',
    'font.size': 9, 'axes.labelsize': 9, 'legend.fontsize': 8, 'xtick.labelsize': 8, 'ytick.labelsize': 8,
    'axes.edgecolor': '#52514e', 'axes.linewidth': 0.6, 'xtick.color': '#52514e', 'ytick.color': '#52514e',
    'axes.grid': True, 'grid.color': '#e4e3df', 'grid.linewidth': 0.5, 'lines.linewidth': 1.2,
    'legend.frameon': False, 'savefig.dpi': 300, 'axes.spines.top': False, 'axes.spines.right': False})
B, O, A = '#2a78d6', '#eb6834', '#1baf7a'
W = 5.8


def edge_window(model, tend, nper=3):
    t, g = simsig(model, 'VGS')
    m = (t > tend - (nper + 1.2) * 25e-6) & (t < tend)
    tt, gg = t[m], g[m]
    r = np.where((gg[1:] > 0.5) & (gg[:-1] <= 0.5))[0]
    t0 = tt[r[0] + 1]
    return t0 - 2e-6, t0 + nper * 25e-6 + 2e-6, t0


def panels(n, h=1.15):
    fig, ax = plt.subplots(n, 1, figsize=(W, 0.35 + h * n), sharex=True)
    return fig, np.atleast_1d(ax)


def finish(fig, ax, xlabel, name):
    ax[-1].set_xlabel(xlabel)
    for a in ax:
        a.margins(x=0)
    fig.align_ylabels(ax)
    fig.tight_layout(h_pad=0.4)
    fig.savefig(OUT + name, bbox_inches='tight')
    plt.close(fig)
    print('saved', name)


def P(a, t, y, t0, c=B, lab=None, ls='-'):
    a.plot((t - t0) * 1e6, y, color=c, label=lab, ls=ls)


def env(a, t, y, c=B, nb=1500, lab=None):
    edges = np.linspace(t[0], t[-1], nb + 1)
    idx = np.searchsorted(t, edges)
    mn = np.array([y[idx[i]:max(idx[i + 1], idx[i] + 1)].min() for i in range(nb)])
    mx = np.array([y[idx[i]:max(idx[i + 1], idx[i] + 1)].max() for i in range(nb)])
    av = np.array([y[idx[i]:max(idx[i + 1], idx[i] + 1)].mean() for i in range(nb)])
    tc = 0.5 * (edges[1:] + edges[:-1]) * 1e3
    a.fill_between(tc, mn, mx, color=c, alpha=0.3, lw=0)
    a.plot(tc, av, color=c, lw=0.9, label=lab)


def vgs(a, m, a0, a1, t0):
    t, g = simsig(m, 'VGS'); t, g = win(t, g, a0, a1)
    P(a, t, g, t0); a.set_ylabel('$V_{GS}$ (p.u.)'); a.set_ylim(-0.15, 1.25)


# ---------- open loop key waveforms (cf. Fig. 3 of the paper)
m = 'research_paper'; a0, a1, t0 = edge_window(m, 0.05)
fig, ax = panels(4)
vgs(ax[0], m, a0, a1, t0)
t, i = sig(m + '_cap_ind_curr', 'Demux6/13'); t, i = win(t, -i, a0, a1); P(ax[1], t, i, t0); ax[1].set_ylabel('$i_{L1}=i_{L2}$ (A)')
t, v = sig(m + '_cap_ind_vol', 'Demux6/6'); t, v = win(t, -v, a0, a1); P(ax[2], t, v, t0); ax[2].set_ylabel('$V_{L1}=V_{L2}$ (V)')
t, v = simsig(m, 'VDS'); t, v = win(t, v, a0, a1); P(ax[3], t, v, t0); ax[3].set_ylabel('$V_{DS}$ (V)')
finish(fig, ax, 'Time (µs), open loop, D = 0.474', 'fig_ol_key.png')

# ---------- open loop diode voltages
fig, ax = panels(4)
vgs(ax[0], m, a0, a1, t0)
for a, (k1, l1), (k2, l2) in [(ax[1], ('1', '$V_{D1}$'), ('2', '$V_{D2}$')), (ax[2], ('4', '$V_{D4}$'), ('', '$V_{Do}$')),
                              (ax[3], ('3', '$V_{D3}$'), ('5', '$V_{D5}$'))]:
    t, v = sig(m + '_diode_vol', f'Demux{k1}/2'); t, v = win(t, -v, a0, a1); P(a, t, v, t0, B, l1)
    t, v = sig(m + '_diode_vol', f'Demux{k2}/2'); t, v = win(t, -v, a0, a1); P(a, t, v, t0, O, l2, '--')
    a.set_ylabel('Reverse V (V)'); a.legend(loc='center left', bbox_to_anchor=(1.0, 0.5), handlelength=1.6)
finish(fig, ax, 'Time (µs), open loop, D = 0.474 (reverse voltage plotted positive)', 'fig_ol_diode.png')

# ---------- open loop capacitor voltages over the whole run
fig, ax = panels(3, 1.0)
t, v = sig(m + '_cap_ind_vol', 'Demux6/1'); env(ax[0], t, v); ax[0].set_ylabel('$V_o$ (V)')
for k, c, l in [(3, B, '$V_{C2}$'), (4, O, '$V_{C3}$'), (5, A, '$V_{C4}$')]:
    t, v = sig(m + '_cap_ind_vol', f'Demux6/{k}'); env(ax[1], t, v, c, lab=l)
ax[1].set_ylabel('$V_{C2}$–$V_{C4}$ (V)'); ax[1].legend(loc='upper right', ncol=3)
t, v = sig(m + '_cap_ind_vol', 'Demux6/2'); env(ax[2], t, v); ax[2].set_ylabel('$V_{C1}$ (V)')
finish(fig, ax, 'Time (ms), open loop', 'fig_ol_caps.png')

# ---------- input current with / without CMRCC
fig, ax = panels(2, 1.3)
for a, mm, lab in [(ax[0], 'research_paper', 'Without CMRCC'), (ax[1], 'research_paper_cmrcc', 'With CMRCC')]:
    b0, b1, tt0 = edge_window(mm, 0.05)
    t, i = sig(mm + '_input_curr'); t, i = win(t, i, b0, b1); P(a, t, i, tt0)
    a.set_ylabel('$I_{in}$ (A)'); a.set_ylim(0, 20)
    a.text(0.01, 0.9, f'{lab}: peak-to-peak ripple {i.max() - i.min():.2f} A', transform=a.transAxes, color='#0b0b0b', fontsize=8)
finish(fig, ax, 'Time (µs), open loop', 'fig_iin_compare.png')

# ---------- CMRCC open loop: IP, IS, Iin
m = 'research_paper_cmrcc'; a0, a1, t0 = edge_window(m, 0.05)
fig, ax = panels(3)
t, i = sig(m + '_mutual_ind_curr'); t, i = win(t, i, a0, a1); P(ax[0], t, i, t0); ax[0].set_ylabel('$I_P$ (A)')
t, i = sig(m + '_cb_curr'); t, i = win(t, i, a0, a1); P(ax[1], t, i, t0); ax[1].set_ylabel('$I_S$ (A)')
t, i = sig(m + '_input_curr'); t, i = win(t, i, a0, a1); P(ax[2], t, i, t0); ax[2].set_ylabel('$I_{in}$ (A)'); ax[2].set_ylim(6, 9)
finish(fig, ax, 'Time (µs), open loop with CMRCC, D = 0.477', 'fig_cmrcc_ol.png')

# ---------- closed loop: VGS, Vo, Io, VDS
m = 'research_paper_closed_loop'; a0, a1, t0 = edge_window(m, 0.05)
fig, ax = panels(4)
vgs(ax[0], m, a0, a1, t0)
t, v = sig(m + '_out_vol'); t, v = win(t, v, a0, a1); P(ax[1], t, v, t0); ax[1].set_ylabel('$V_o$ (V)'); ax[1].set_ylim(399, 401)
t, i = sig(m + '_output_Curr'); t, i = win(t, i, a0, a1); P(ax[2], t, i, t0); ax[2].set_ylabel('$I_o$ (A)'); ax[2].set_ylim(0.670, 0.680)
t, v = simsig(m, 'VDS'); t, v = win(t, v, a0, a1); P(ax[3], t, v, t0); ax[3].set_ylabel('$V_{DS}$ (V)')
finish(fig, ax, 'Time (µs), closed loop, 270 W', 'fig_cl_vo.png')

for name, items in [('fig_cl_diode1.png', [('1', '$V_{D1}$'), ('2', '$V_{D2}$'), ('3', '$V_{D3}$')]),
                    ('fig_cl_diode2.png', [('4', '$V_{D4}$'), ('5', '$V_{D5}$'), ('', '$V_{Do}$')])]:
    fig, ax = panels(4)
    vgs(ax[0], m, a0, a1, t0)
    for a, (k, l) in zip(ax[1:], items):
        t, v = sig(m + '_diode_vol', f'Demux{k}/2'); t, v = win(t, -v, a0, a1); P(a, t, v, t0); a.set_ylabel(l + ' (V)')
    finish(fig, ax, 'Time (µs), closed loop, 270 W (reverse voltage plotted positive)', name)

# ---------- closed loop CMRCC currents (IS = Iin - IP, both measured)
fig, ax = panels(4)
vgs(ax[0], m, a0, a1, t0)
t, ip = sig(m + '_mutual_ind_curr'); _, ii = sig(m + '_input_curr')
tw, ipw = win(t, ip, a0, a1); _, iiw = win(t, ii, a0, a1)
P(ax[1], tw, ipw, t0); ax[1].set_ylabel('$I_P$ (A)')
P(ax[2], tw, iiw - ipw, t0); ax[2].set_ylabel('$I_S$ (A)')
P(ax[3], tw, iiw, t0); ax[3].set_ylabel('$I_{in}$ (A)'); ax[3].set_ylim(6, 9)
finish(fig, ax, 'Time (µs), closed loop, 270 W', 'fig_cl_cmrcc.png')

# ---------- closed loop start-up
fig, ax = panels(2, 1.3)
t, v = sig(m + '_out_vol'); env(ax[0], t, v); ax[0].set_ylabel('$V_o$ (V)'); ax[0].axhline(400, color='#52514e', lw=0.6, ls=':')
t, d = simsig(m, 'Duty'); ax[1].plot(t * 1e3, d, color=B); ax[1].set_ylabel('Duty ratio $D$')
finish(fig, ax, 'Time (ms), closed-loop start-up', 'fig_cl_startup.png')

# ---------- load step 160 W -> 270 W
m = 'research_paper_closed_loop_load_step'
fig, ax = panels(4, 1.05)
t, v = sig(m + '_output_vol'); t, v = win(t, v, 0.03, 0.14); env(ax[0], t, v); ax[0].set_ylabel('$V_o$ (V)'); ax[0].set_ylim(390, 410)
t, i = sig(m + '_output_curr'); t, i = win(t, i, 0.03, 0.14); env(ax[1], t, i); ax[1].set_ylabel('$I_o$ (A)')
t, i = sig(m + '_input_curr'); t, i = win(t, i, 0.03, 0.14); env(ax[2], t, i); ax[2].set_ylabel('$I_{in}$ (A)')
t, d = simsig(m, 'Duty'); t, d = win(t, d, 0.03, 0.14); ax[3].plot(t * 1e3, d, color=B); ax[3].set_ylabel('Duty ratio $D$')
for a in ax:
    a.axvline(40, color='#52514e', lw=0.6, ls=':')
ax[0].annotate('load step at 40 ms', xy=(40, 397.5), xytext=(55, 393), fontsize=8,
               arrowprops=dict(arrowstyle='->', color='#52514e', lw=0.6))
finish(fig, ax, 'Time (ms)', 'fig_ls.png')

fig, ax = panels(1, 1.7)
t, v = sig(m + '_output_vol'); t, v = win(t, v, 0.038, 0.05)
env(ax[0], t, v, nb=480); ax[0].set_ylabel('$V_o$ (V)')
ax[0].axhline(400, color='#52514e', lw=0.6, ls=':')
finish(fig, ax, 'Time (ms), detail around the load step', 'fig_ls_zoom.png')

t, d = simsig(m, 'Duty')
tc, dc = simsig('research_paper_closed_loop', 'Duty')
_, vds_cl = simsig('research_paper_closed_loop', 'VDS')
_, vds_ol = simsig('research_paper', 'VDS')
res = {'D_pre': d[(t > 0.035) & (t < 0.04)].mean(), 'D_post': d[t > 0.13].mean(), 'D_cl': dc[-200:].mean(),
       'D_cl_max': dc.max(), 'D_cl_min': dc.min(),
       'VDS_cl_peak': vds_cl[-100000:].max(), 'VDS_cl_plateau': np.percentile(vds_cl[-100000:], 90),
       'VDS_ol_peak': vds_ol[-100000:].max(), 'VDS_ol_plateau': np.percentile(vds_ol[-100000:], 90)}
res = {k: float(v) for k, v in res.items()}
json.dump(res, open(os.path.join(ROOT, 'results', 'logged_signal_metrics.json'), 'w'), indent=1)
print(res)
