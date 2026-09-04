from datetime import datetime
import numpy as np
from config import Config
from ml.classifier import ClassificationResult,TopPrediction
from state import State,StateMachine
from service import DogwatchService
class Clock:
 def __init__(self):self.t=0
 def __call__(self):return self.t
class Player:
 def __init__(self):self.calls=0
 def play(self,path):self.calls+=1
class Classifier:pass
class WebsiteClassifier:
 def classify(self,waveform,top_k=10):
  return ClassificationResult(
   .0,
   (TopPrediction("Dog",.35,69),TopPrediction("Animal",.34,67),TopPrediction("Bark",.02,70)),
   np.zeros((1,521),dtype=np.float32),
   np.zeros((1,1024),dtype=np.float32),
   1.0,
   {"Animal":.34,"Domestic animals, pets":.31,"Dog":.35,"Bark":.02,"Yip":0.0,"Howl":0.0,"Bow-wow":0.0,"Growling":0.0,"Whimper (dog)":0.0,"Canidae, dogs, wolves":0.0},
  )
def test_all_state_transitions():
 c=Clock();s=StateMachine(False,c);assert s.state==State.DISABLED;s.set_enabled(True);assert s.state==State.LISTENING;s.bark_counted();assert s.state==State.COUNTING;s.playback_started();assert s.state==State.PLAYING;s.playback_finished(1,2);assert s.state==State.COOLDOWN;c.t=3;assert s.tick()==State.LISTENING;s.set_enabled(False);assert s.state==State.DISABLED
def test_playback_and_cooldown_reject_real_or_simulated():
 c=Clock();svc=DogwatchService(Config(required_barks=1,cooldown_s=2,post_playback_suppression_s=1),Classifier(),Player(),c)
 svc.state.playback_started();assert not svc.handle_bark_event(0,datetime(2024,1,1,23));svc.state.playback_finished(1,2);assert not svc.handle_bark_event(0,datetime(2024,1,1,23));c.t=3;assert svc.handle_bark_event(3,datetime(2024,1,1,23));svc._play_thread.join()
def test_config_boundary_clears():
 c=Clock();svc=DogwatchService(Config(),Classifier(),Player(),c);svc.counter.events.append(1);svc.segmenter.onset=1;svc.update_config(Config());assert not svc.counter.events and svc.segmenter.onset is None
def test_daytime_barks_register_without_playback():
 c=Clock();player=Player();svc=DogwatchService(Config(required_barks=1),Classifier(),player,c)
 assert svc.handle_bark_event(0,datetime(2024,1,1,15))
 assert svc.status()["bark_count"]==1
 assert player.calls==0
def test_website_style_detection_accumulates_yamnet_windows():
 c=Clock();player=Player()
 svc=DogwatchService(Config(required_barks=2,website_detection_debounce_s=4,bark_on_threshold=.3,rms_gate_dbfs=None),WebsiteClassifier(),player,c)
 block=np.ones(4800,dtype=np.float32)*.01
 for _ in range(10):
  svc.process_audio(block,48000); c.t+=.1
 assert svc.status()["bark_count"]==0
 for _ in range(12):
  svc.process_audio(block,48000); c.t+=.1
 assert svc.status()["bark_count"]==1
 for _ in range(30):
  svc.process_audio(block,48000); c.t+=.1
 assert svc.status()["bark_count"]==1
 for _ in range(20):
  svc.process_audio(block,48000); c.t+=.1
 assert svc.status()["bark_count"]==2
