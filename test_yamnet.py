#!/usr/bin/env python3
"""Validate the real YAMNet model against a user-supplied WAV."""
import argparse,sys,time
from pathlib import Path
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument("wav",type=Path);p.add_argument("--interval",type=float,default=1.0);a=p.parse_args(argv)
 try:
  from scipy.io import wavfile
  from audio.processing import resample_audio
  from ml.yamnet_classifier import YAMNetClassifier
  rate,data=wavfile.read(a.wav)
  if data.ndim not in (1,2) or rate<=0:raise ValueError("unsupported WAV layout")
  audio=resample_audio(data,rate); model=YAMNetClassifier()
  step=max(16000,int(a.interval*16000))
  for pos in range(0,len(audio),step):
   chunk=audio[pos:pos+step]
   if not len(chunk):continue
   r=model.classify(chunk); print(f"{pos/16000:7.2f}s bark={r.bark_score:.4f}  "+", ".join(f"{x.label}={x.score:.3f}" for x in r.top_predictions))
  print("latency:",model.latency_stats());return 0
 except FileNotFoundError:print(f"error: WAV not found: {a.wav}",file=sys.stderr)
 except (ValueError,OSError) as exc:print(f"error: unsupported or corrupt WAV: {exc}",file=sys.stderr)
 except Exception as exc:print(f"error: YAMNet validation failed: {exc}",file=sys.stderr)
 return 2
if __name__=="__main__":raise SystemExit(main())
