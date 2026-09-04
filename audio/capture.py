from __future__ import annotations
import logging,queue
import numpy as np
class MicrophonePermissionError(RuntimeError): pass
class AudioCapture:
 def __init__(self,sample_rate=48000,blocksize=4800,queue_size=8,device=None): self.sample_rate=sample_rate; self.blocksize=blocksize; self.device=device; self.queue=queue.Queue(queue_size); self.stream=None; self.callback_errors=queue.Queue(); self.dropped=0
 def _callback(self,indata,frames,time_info,status):
  if status:
   try:self.callback_errors.put_nowait(str(status))
   except queue.Full:pass
  try:self.queue.put_nowait(np.array(indata,copy=True))
  except queue.Full:self.dropped+=1
 def start(self):
  import sounddevice as sd
  try:
   info=sd.query_devices(self.device,"input"); logging.info("microphone_selected",extra={"device":info["name"],"sample_rate":self.sample_rate})
   self.stream=sd.InputStream(device=self.device,samplerate=self.sample_rate,channels=1,dtype="float32",blocksize=self.blocksize,callback=self._callback); self.stream.start()
  except Exception as exc:
   raise MicrophonePermissionError("Cannot open microphone. In macOS System Settings > Privacy & Security > Microphone, enable access for Terminal (or the app launching Dogwatch), then restart it. Original error: "+str(exc)) from exc
 def read(self,timeout=.5):
  try:return self.queue.get(timeout=timeout)
  except queue.Empty:return None
 def stop(self):
  if self.stream:self.stream.stop(); self.stream.close(); self.stream=None
