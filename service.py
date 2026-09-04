"""Application orchestration: components remain independently testable."""
from __future__ import annotations
from dataclasses import asdict
from datetime import datetime
import logging,math,threading,time
import numpy as np
from detection.bark_counter import BarkCounter
from detection.acoustic_bark import acoustic_bark_score
from detection.bark_event import BarkEventSegmenter
from scheduler import is_quiet_time
from state import StateMachine,State
WINDOW_SIZE=15360
HOP_SIZE=7680
class DogwatchService:
 def __init__(self,config,classifier,player,clock=time.monotonic):
  self.config=config; self.classifier=classifier; self.player=player; self.clock=clock; self.state=StateMachine(config.enabled,clock); self._build_detection(); self.last_score=0.; self.last_model_score=0.; self.last_acoustic_score=0.; self.last_dbfs=float("-inf"); self.last_gated=False; self.last_top_predictions=[]; self.last_dog_scores={}; self._play_thread=None; self._wave_buffer=np.zeros(0,dtype=np.float32); self._prediction_buffer=[]; self._last_website_event=None
 def _build_detection(self):
  c=self.config; self.segmenter=BarkEventSegmenter(c.bark_on_threshold,c.bark_off_threshold,c.min_event_duration_s,c.release_duration_s,c.min_event_gap_s); self.counter=BarkCounter(c.rolling_window_s,c.required_barks)
 def update_config(self,config): self.config=config; self.state.set_enabled(config.enabled); self._build_detection(); self._wave_buffer=np.zeros(0,dtype=np.float32); self._prediction_buffer=[]; self._last_website_event=None
 def process_audio(self,audio,rate,timestamp=None):
  from audio.processing import dc_removed_peak_normalized,prepare_audio
  if not self.state.accepts_bark():return
  wave,db,gated=prepare_audio(audio,rate,self.config.rms_gate_dbfs); self.last_dbfs=db; self.last_gated=gated
  if gated:return
  self._wave_buffer=np.concatenate((self._wave_buffer,wave.astype(np.float32,copy=False)))
  while self._wave_buffer.size>=WINDOW_SIZE:
   window=self._wave_buffer[:WINDOW_SIZE].copy()
   self._wave_buffer=self._wave_buffer[HOP_SIZE:]
   model_wave=dc_removed_peak_normalized(window,self.config.yamnet_peak_normalize_min_dbfs) if self.config.yamnet_peak_normalize else window
   result=self.classifier.classify(model_wave,top_k=10); self._prediction_buffer.append(result)
   if len(self._prediction_buffer)>=2:
    self._handle_prediction_pair(window,timestamp)
    self._prediction_buffer=[]
 def _handle_prediction_pair(self,window,timestamp=None):
  results=self._prediction_buffer[-2:]
  dog_scores={}
  for result in results:
   for label,score in (result.dog_scores or {}).items():
    dog_scores.setdefault(label,[]).append(score)
  dog_scores={label:float(np.mean(scores)) for label,scores in dog_scores.items()}
  top_by_label={}
  for result in results:
   for pred in result.top_predictions:
    top_by_label[pred.label]=(pred.index,max(pred.score,top_by_label.get(pred.label,(pred.index,0.0))[1]))
  self.last_top_predictions=[{"label":label,"score":float(score),"index":int(index)} for label,(index,score) in sorted(top_by_label.items(),key=lambda x:x[1][1],reverse=True)[:10]]
  self.last_dog_scores=dict(sorted(dog_scores.items(),key=lambda x:x[1],reverse=True))
  specific=max((dog_scores.get(label,0.0) for label in ("Dog","Bark","Yip","Howl","Bow-wow","Growling","Whimper (dog)","Canidae, dogs, wolves")),default=0.0)
  general=max((dog_scores.get(label,0.0) for label in ("Animal","Domestic animals, pets")),default=0.0)
  any_dog=max(dog_scores.values(),default=0.0)
  website_detect=specific>self.config.dog_specific_floor and (any_dog>=self.config.bark_on_threshold or general>=self.config.bark_on_threshold)
  website_score=any_dog if website_detect else 0.0
  self.last_model_score=website_score
  self.last_acoustic_score=acoustic_bark_score(window,16000) if self.config.acoustic_detector_enabled else 0.
  self.last_score=max(self.last_model_score,self.last_acoustic_score)
  ts=self.clock() if timestamp is None else timestamp
  if website_detect:
   if self._last_website_event is None or ts-self._last_website_event>=self.config.website_detection_debounce_s:
    self._last_website_event=ts; self.handle_bark_event(ts)
   return
  event=self.segmenter.update(self.last_score,ts)
  if event:self.handle_bark_event(event.end)
 def handle_bark_event(self,timestamp=None,now=None):
  """Single entry point for real and simulated finalized events."""
  if not self.state.accepts_bark():return False
  wall=now or datetime.now()
  ts=self.clock() if timestamp is None else timestamp
  self.state.bark_counted()
  triggered=self.counter.add(ts)
  if not is_quiet_time(wall,self.config.quiet_start,self.config.quiet_end):return True
  if triggered:self._trigger(); return True
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
 def status(self):
  dbfs=self.last_dbfs if math.isfinite(self.last_dbfs) else None
  quiet=is_quiet_time(datetime.now(),self.config.quiet_start,self.config.quiet_end)
  return {"state":self.state.tick().value,"bark_count":self.counter.count(self.clock()),"last_bark_score":self.last_score,"last_model_score":self.last_model_score,"last_acoustic_score":self.last_acoustic_score,"last_dbfs":dbfs,"last_gated":self.last_gated,"quiet_active":quiet,"top_predictions":self.last_top_predictions,"dog_scores":self.last_dog_scores,"enabled":self.config.enabled}
