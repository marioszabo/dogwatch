from abc import ABC,abstractmethod
from pathlib import Path
import logging,subprocess,wave
class PlaybackError(RuntimeError): pass
class AudioPlayer(ABC):
 @abstractmethod
 def play(self,path:str|Path)->None: ...
class MacOSAudioPlayer(AudioPlayer):
 def validate(self,path):
  p=Path(path).expanduser()
  if not p.is_file():raise PlaybackError(f"response audio not found: {p}; record or copy a WAV/AIFF file there")
  if p.stat().st_size==0:raise PlaybackError(f"response audio is empty: {p}")
  return p
 def play(self,path):
  p=self.validate(path); logging.info("response_playback_started",extra={"path":str(p)})
  try: subprocess.run(["/usr/bin/afplay",str(p)],check=True)
  except (OSError,subprocess.CalledProcessError) as exc: logging.exception("response_playback_failed",extra={"path":str(p)}); raise PlaybackError(str(exc)) from exc
  logging.info("response_playback_finished",extra={"path":str(p)})
