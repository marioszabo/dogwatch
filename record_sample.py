#!/usr/bin/env python3
import argparse
from pathlib import Path
import sounddevice as sd
import soundfile as sf
def main(argv=None):
 p=argparse.ArgumentParser(description="Record a bounded microphone sample entirely to the requested WAV path")
 p.add_argument("output",type=Path,help="explicit output .wav path");p.add_argument("--duration",type=float,default=5);p.add_argument("--rate",type=int,default=48000);a=p.parse_args(argv)
 if a.output.suffix.lower()!='.wav':p.error("output must end in .wav")
 if not 0.1<=a.duration<=60:p.error("duration must be between 0.1 and 60 seconds")
 if a.output.exists():p.error("refusing to overwrite existing output")
 a.output.parent.mkdir(parents=True,exist_ok=True)
 try:data=sd.rec(round(a.duration*a.rate),samplerate=a.rate,channels=1,dtype='float32',blocking=True);sf.write(a.output,data,a.rate,subtype='PCM_16')
 except Exception as exc:p.error("microphone recording failed; grant Terminal microphone permission in macOS System Settings > Privacy & Security > Microphone: "+str(exc))
 print(f"saved {a.duration:.1f}s to {a.output}");return 0
if __name__=='__main__':raise SystemExit(main())
