import numpy as np
from audio.processing import prepare_audio,resample_audio,rms_dbfs,to_mono_float32
def test_generated_stereo_resamples_and_sanitizes():
 x=np.column_stack([np.sin(np.arange(4800)*2*np.pi*440/48000),np.full(4800,np.nan)])
 mono=to_mono_float32(x);y=resample_audio(mono,48000);assert y.dtype==np.float32 and len(y)==1600 and np.isfinite(y).all()
def test_rms_and_gate():
 x=np.ones(1600,dtype='float32')*.001;r,db=rms_dbfs(x);assert abs(db+60)<.01
 y,_,g=prepare_audio(x,16000,-55);assert g and not y.any()
