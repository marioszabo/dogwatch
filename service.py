"""Application orchestration: components remain independently testable."""
from __future__ import annotations
from dataclasses import asdict
from datetime import datetime
import logging,threading,time
from detection.bark_counter import BarkCounter
from detection.bark_event import BarkEventSegmenter
from scheduler import is_quiet_time
from state import StateMachine,State
class DogwatchService:
 def __init__(self,config,classifier,player,clock=time.monotonic):
  self.config=config; self.classifier=classifier; self.player=player; self.clock=clock; self.state=StateMachine(config.enabled,clock); self._build_detection(); self.last_score=0.; self.last_dbfs=float("-inf"); self._play_thread=None
 def _build_detection(self):
  c=self.config; self.segmenter=BarkEventSegmenter(c.bark_on_threshold,c.bark_off_threshold,c.min_event_duration_s,c.release_duration_s,c.min_event_gap_s); self.counter=BarkCounter(c.rolling_window_s,c.required_barks)
 def update_config(self,config): self.config=config; self.state.set_enabled(config.enabled); self._build_detection()
 def process_audio(self,audio,rate,timestamp=None):
  from audio.processing import prepare_audio
  if not self.state.accepts_bark():return
  wave,db,gated=prepare_audio(audio,rate,self.config.rms_gate_dbfs); self.last_dbfs=db
  if gated:return
  result=self.classifier.classify(wave); self.last_score=result.bark_score; ts=self.clock() if timestamp is None else timestamp
  event=self.segmenter.update(result.bark_score,ts)
  if event:self.handle_bark_event(event.end)
 def handle_bark_event(self,timestamp=None,now=None):
  """Single entry point for real and simulated finalized events."""
  if not self.state.accepts_bark():return False
  wall=now or datetime.now()
  if not is_quiet_time(wall,self.config.quiet_start,self.config.quiet_end):return False
  ts=self.clock() if timestamp is None else timestamp
  self.state.bark_counted()
  if self.counter.add(ts):self._trigger(); return True
  return False
 def _trigger(self):
  self.counter.clear(); self.segmenter.reset()
  if not self.state.playback_started():return
  def run():
   try:self.player.play(self.config.response_path)
   except Exception:logging.exception("playback lifecycle failed")
   finally:self.state.playback_finished(self.config.post_playback_suppression_s,self.config.cooldown_s)
  self._play_thread=threading.Thread(target=run,name="playback",daemon=True); self._play_thread.start()
 def test_response(self):
  if not self.state.playback_started():return False
  self.counter.clear(); self.segmenter.reset()
  def run():
   try:self.player.play(self.config.response_path)
   except Exception:logging.exception("response test failed")
   finally:self.state.playback_finished(self.config.post_playback_suppression_s,self.config.cooldown_s)
  self._play_thread=threading.Thread(target=run,daemon=True); self._play_thread.start(); return True
 def status(self): return {"state":self.state.tick().value,"bark_count":self.counter.count(self.clock()),"last_bark_score":self.last_score,"last_dbfs":self.last_dbfs,"enabled":self.config.enabled}
