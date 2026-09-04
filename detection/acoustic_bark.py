"""Local acoustic bark-burst scoring.

This is deliberately simple: it does not replace YAMNet, but catches short,
sharp bark-like bursts that YAMNet may label as generic sound effects.
"""
from __future__ import annotations

import numpy as np
from scipy.signal import stft


def acoustic_bark_score(audio: np.ndarray, sample_rate: int) -> float:
    x=np.asarray(audio,dtype=np.float32).reshape(-1)
    if sample_rate<=0 or x.size < sample_rate*.15:return 0.0
    x=np.nan_to_num(x,nan=0.0,posinf=1.0,neginf=-1.0)
    frame=max(256,int(sample_rate*.025)); hop=max(128,int(sample_rate*.010))
    if x.size < frame:return 0.0
    windows=np.lib.stride_tricks.sliding_window_view(x,frame)[::hop]
    if len(windows)<3:return 0.0
    rms=np.sqrt(np.mean(np.square(windows,dtype=np.float64),axis=1))
    peak=float(np.max(rms))
    overall=float(np.sqrt(np.mean(np.square(x,dtype=np.float64)))+1e-12)
    median=float(np.median(rms)+1e-9)
    if peak < .003:return 0.0
    burst_ratio=peak/median
    above=rms > max(median*3.0,peak*.35)
    if np.any(above):
        idx=np.flatnonzero(above)
        duration=(idx[-1]-idx[0]+1)*hop/sample_rate
    else:
        duration=x.size/sample_rate
    burstiness=np.clip((burst_ratio-3.0)/10.0,0.0,1.0)
    duration_score=1.0 if .08 <= duration <= .80 else max(0.0,1.0-abs(duration-.30)/1.20)
    f,_,z=stft(x,fs=sample_rate,nperseg=frame,noverlap=frame-hop,boundary=None)
    power=np.abs(z)**2
    total=np.sum(power)+1e-12
    bark_band=np.sum(power[(f>=250)&(f<=4000)])
    very_low=np.sum(power[f<120])
    bark_ratio=bark_band/total
    high_ratio=np.sum(power[(f>=900)&(f<=5000)])/total
    band_score=np.clip((bark_ratio-.22)/.55,0.0,1.0)
    high_score=np.clip((high_ratio-.12)/.45,0.0,1.0)
    energy_dbfs=20*np.log10(overall)
    energy_score=np.clip((energy_dbfs+58)/34,0.0,1.0)
    modulation=np.std(rms)/(float(np.mean(rms))+1e-9)
    modulation_score=np.clip((modulation-.15)/1.25,0.0,1.0)
    low_penalty=np.clip((very_low/total-.35)/.30,0.0,.5)
    burst_score=(.35*burstiness)+(.25*duration_score)+(.25*band_score)+(.15*high_score)
    sustained_score=(.35*energy_score)+(.25*band_score)+(.20*high_score)+(.20*modulation_score)
    return float(np.clip(max(burst_score,sustained_score)-low_penalty,0.0,1.0))
