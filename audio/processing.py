"""Audio normalization for YAMNet. dBFS is digital full scale, not acoustic SPL."""
from __future__ import annotations
import numpy as np
from scipy.signal import resample_poly
from math import gcd

def to_mono_float32(audio: np.ndarray) -> np.ndarray:
    x=np.asarray(audio)
    if x.ndim not in (1,2): raise ValueError("audio must have one sample dimension and optional channels")
    if np.issubdtype(x.dtype,np.integer):
        info=np.iinfo(x.dtype); x=x.astype(np.float32)/max(abs(info.min),info.max)
    else: x=x.astype(np.float32,copy=False)
    if x.ndim==2: x=x.mean(axis=1,dtype=np.float32)
    return np.nan_to_num(x,nan=0.0,posinf=1.0,neginf=-1.0).clip(-1,1).astype(np.float32)

def resample_audio(audio: np.ndarray, source_rate: int, target_rate: int=16000) -> np.ndarray:
    if source_rate <= 0 or target_rate <= 0: raise ValueError("sample rates must be positive")
    x=to_mono_float32(audio)
    if source_rate==target_rate:return x
    g=gcd(source_rate,target_rate)
    return resample_poly(x,target_rate//g,source_rate//g).astype(np.float32)

def rms_dbfs(audio: np.ndarray) -> tuple[float,float]:
    x=to_mono_float32(audio); rms=float(np.sqrt(np.mean(np.square(x,dtype=np.float64)))) if x.size else 0.0
    return rms, (20*np.log10(rms) if rms>0 else float("-inf"))

def prepare_audio(audio: np.ndarray, source_rate: int, gate_dbfs: float|None=None) -> tuple[np.ndarray,float,bool]:
    x=resample_audio(audio,source_rate); _,db=rms_dbfs(x); gated=gate_dbfs is not None and db < gate_dbfs
    return (np.zeros_like(x) if gated else x),db,gated
