"""Steady-state, transient, ripple and loss metrics from the extracted scope data.
Writes results/steady_state_metrics.json and results/ripple_and_losses.json."""
import os, json
import numpy as np
from load_data import sig, win, ROOT
M={}
def ss(fig,name=None,a=0.045,b=0.05):
    t,y=sig(fig,name); return win(t,y,a,b)
for tag,pre,(a,b) in [('OL','research_paper',(0.045,0.05)),('CM','research_paper_cmrcc',(0.045,0.05)),('CL','research_paper_closed_loop',(0.045,0.05)),('LS','research_paper_closed_loop_load_step',(0.135,0.14))]:
    r={}
    cv = pre+'_cap_ind_vol'; ci = pre+('_closed_loop_cap_ind_Curr'[len('_closed_loop'):] if tag=='CL' else '_cap_ind_curr')
    if tag=='CL': ci='research_paper_closed_loop_cap_ind_Curr'
    names=['Co','C1','C2','C3','C4','L1','L2']
    for i,nm in enumerate(names):
        _,v=ss(cv,f'Demux6/{i+1}',a,b); _,c=ss(ci,f'Demux6/{i+8}',a,b)
        r['V'+nm]=dict(mean=v.mean(),min=v.min(),max=v.max(),p1=np.percentile(v,2),p99=np.percentile(v,98))
        r['I'+nm]=dict(mean=c.mean(),min=c.min(),max=c.max(),p1=np.percentile(c,2),p99=np.percentile(c,98))
    dv = pre+'_diode_vol'; dc = pre+'_diode_curr'
    for k,lab in [('', 'Do'),('1','D1'),('2','D2'),('3','D3'),('4','D4'),('5','D5')]:
        _,v=ss(dv,f'Demux{k}/2',a,b); _,c=ss(dc,f'Demux{k}/1',a,b)
        blk=-v
        r['V'+lab]=dict(block_max=blk.max(), block_plateau=np.percentile(blk,90), frac_blocking=float((blk>0.5*blk.max()).mean()))
        r['I'+lab]=dict(mean=c.mean(),peak=c.max(),rms=np.sqrt((c**2).mean()))
    # outputs
    ov={'OL':'research_paper_output_vol','CM':'research_paper_cmrcc_out_vol','CL':'research_paper_closed_loop_out_vol','LS':'research_paper_closed_loop_load_step_output_vol'}[tag]
    oc={'OL':'research_paper_output_curr','CM':'research_paper_cmrcc_out_curr','CL':'research_paper_closed_loop_output_Curr','LS':'research_paper_closed_loop_load_step_output_curr'}[tag]
    ic={'OL':'research_paper_input_curr','CM':'research_paper_cmrcc_input_curr','CL':'research_paper_closed_loop_input_curr','LS':'research_paper_closed_loop_load_step_input_curr'}[tag]
    _,vo=ss(ov,None,a,b); _,io=ss(oc,None,a,b); _,ii=ss(ic,None,a,b)
    r['Vo']=dict(mean=vo.mean(),pp=vo.max()-vo.min()); r['Io']=dict(mean=io.mean()); 
    r['Iin']=dict(mean=ii.mean(),pp=ii.max()-ii.min(),p2_98=np.percentile(ii,99)-np.percentile(ii,1),std=ii.std())
    r['Po']=vo.mean()*io.mean(); r['Pin']=48*ii.mean(); r['eff']=r['Po']/r['Pin']
    if tag!='OL':
        ip={'CM':'research_paper_cmrcc_mutual_ind_curr','CL':'research_paper_closed_loop_mutual_ind_curr','LS':'research_paper_closed_loop_load_step_mutual_ind_curr'}[tag]
        _,p=ss(ip,None,a,b); r['IP']=dict(mean=p.mean(),pp=p.max()-p.min(),std=p.std())
        isf={'CM':'research_paper_cmrcc_cb_curr','LS':'research_paper_closed_loop_load_step_cb_curr'}.get(tag)
        if isf: _,q=ss(isf,None,a,b); r['IS']=dict(mean=q.mean(),pp=q.max()-q.min(),min=q.min(),max=q.max())
    if tag=='LS':
        _,vm=ss('research_paper_closed_loop_load_step_mutual_ind_vol',None,a,b); r['VLp']=dict(mean=vm.mean(),min=vm.min(),max=vm.max())
    M[tag]=r
# duty from D3 blocking fraction (D3,D5 block in ON interval)
for tag in M: M[tag]['D_est']=np.mean([M[tag]['VD3']['frac_blocking'],M[tag]['VD5']['frac_blocking']])
# load step transient
t,v=sig('research_paper_closed_loop_load_step_output_vol'); t2,io=sig('research_paper_closed_loop_load_step_output_curr')
pre=(t>0.035)&(t<0.04); post=t>0.04
vref=400.0
M['LSdyn']=dict(Vo_pre=v[pre].mean(), Io_pre=io[(t2>0.035)&(t2<0.04)].mean(), Io_post=io[t2>0.13].mean(),
   Vmin=v[post].min(), t_min=t[post][np.argmin(v[post])], undershoot=vref-v[post].min())
for band in [4.0,2.0,1.0]:
    out=np.where(post & (np.abs(v-vref)>band))[0]
    M['LSdyn'][f'settle_{band}V']=(t[out[-1]]-0.04) if len(out) else 0
# startup of closed loop
t,v=sig('research_paper_closed_loop_out_vol'); M['CLstart']=dict(vmax=v.max(),vmin=v.min(),t_vmax=t[np.argmax(v)])
out=np.where(np.abs(v-400)>4)[0]; M['CLstart']['settle4']=t[out[-1]] if len(out) else 0
t,v=sig('research_paper_closed_loop_load_step_output_vol'); m=t<0.04; M['LSstart']=dict(vmax=v[m].max(),vmin=v[m].min())
def conv(o):
    if isinstance(o,dict): return {k:conv(x) for k,x in o.items()}
    return float(o)
os.makedirs(os.path.join(ROOT, 'results'), exist_ok=True)
json.dump(conv(M), open(os.path.join(ROOT, 'results', 'steady_state_metrics.json'), 'w'), indent=1)



# ---------------- per-period input ripple and loss breakdown (closed loop, 270 W)
from scipy.signal import lfilter


def per_period_pp(fig, a=0.045, b=0.05):
    t, y = win(*sig(fig), a, b); n = int(round(25e-6 / (t[1] - t[0])))
    k = len(y) // n; Y = y[:k * n].reshape(k, n)
    return (Y.max(1) - Y.min(1)).mean(), y.mean()


R = {}
for k, f, ab in [('OL', 'research_paper_input_curr', (0.045, 0.05)), ('CM', 'research_paper_cmrcc_input_curr', (0.045, 0.05)),
                 ('CL', 'research_paper_closed_loop_input_curr', (0.045, 0.05)),
                 ('LS', 'research_paper_closed_loop_load_step_input_curr', (0.135, 0.14))]:
    pp, mean = per_period_pp(f, *ab); R[k] = dict(pp=pp, mean=mean, pct=100 * pp / mean)
for k, f in [('CM', 'research_paper_cmrcc_mutual_ind_curr'), ('CL', 'research_paper_closed_loop_mutual_ind_curr')]:
    pp, mean = per_period_pp(f); R['IP_' + k] = dict(pp=pp, mean=mean)

pre = 'research_paper_closed_loop'
def rms(fig, name=None):
    t, y = win(*sig(fig, name), 0.045, 0.05); return np.sqrt((y ** 2).mean()), y.mean()

# default Specialized Power Systems diode snubber: Rs = 500 ohm, Cs = 250 nF
Rs, Cs, P_snub = 500.0, 250e-9, 0.0
for k in ['', '1', '2', '3', '4', '5']:
    t, v = sig(pre + '_diode_vol', f'Demux{k}/2'); a = np.exp(-(t[1] - t[0]) / (Rs * Cs))
    vc = lfilter([1 - a], [1, -a], v, zi=[a * v[0]])[0]; m_ = t > 0.045
    P_snub += np.mean((v[m_] - vc[m_]) ** 2) / Rs
Lo = {}
iL = rms(pre + '_cap_ind_Curr', 'Demux6/13')[0]; Lo['inductors'] = 2 * 0.12 * iL ** 2
vf = {'1': 0.85, '2': 0.85, '3': 0.12, '4': 0.12, '5': 0.12, '': 0.12}
Lo['diode_cond'] = sum(vf[k] * rms(pre + '_diode_curr', f'Demux{k}/1')[1] + 0.01 * rms(pre + '_diode_curr', f'Demux{k}/1')[0] ** 2 for k in vf)
Lo['cap_esr'] = sum(r * rms(pre + '_cap_ind_Curr', f'Demux6/{k}')[0] ** 2 for k, r in {8: 0.05, 9: 0.003, 10: 0.003, 11: 0.003, 12: 0.003}.items())
t, ip = sig(pre + '_mutual_ind_curr'); _, ii = sig(pre + '_input_curr'); m_ = t > 0.045
ipr, isr = np.sqrt((ip[m_] ** 2).mean()), np.sqrt(((ii - ip)[m_] ** 2).mean())
Lo['cmrcc_windings_CB'] = 0.014 * ipr ** 2 + (0.014 + 0.0055) * isr ** 2
Lo['snubbers'] = P_snub
Lo['Pin'] = M['CL']['Pin']; Lo['Po'] = M['CL']['Po']
Lo['remainder_mosfet_etc'] = Lo['Pin'] - Lo['Po'] - sum(Lo[k] for k in ['inductors', 'diode_cond', 'cap_esr', 'cmrcc_windings_CB', 'snubbers'])
Lo['iL_rms'], Lo['IP_rms'], Lo['IS_rms'] = iL, ipr, isr
R['loss'] = Lo
json.dump(conv(R), open(os.path.join(ROOT, 'results', 'ripple_and_losses.json'), 'w'), indent=1)
print('metrics written to results/')
