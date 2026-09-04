from datetime import datetime
from config import Config
from state import State,StateMachine
from service import DogwatchService
class Clock:
 def __init__(self):self.t=0
 def __call__(self):return self.t
class Player:
 def play(self,path):pass
class Classifier:pass
def test_all_state_transitions():
 c=Clock();s=StateMachine(False,c);assert s.state==State.DISABLED;s.set_enabled(True);assert s.state==State.LISTENING;s.bark_counted();assert s.state==State.COUNTING;s.playback_started();assert s.state==State.PLAYING;s.playback_finished(1,2);assert s.state==State.COOLDOWN;c.t=3;assert s.tick()==State.LISTENING;s.set_enabled(False);assert s.state==State.DISABLED
def test_playback_and_cooldown_reject_real_or_simulated():
 c=Clock();svc=DogwatchService(Config(required_barks=1,cooldown_s=2,post_playback_suppression_s=1),Classifier(),Player(),c)
 svc.state.playback_started();assert not svc.handle_bark_event(0,datetime(2024,1,1,23));svc.state.playback_finished(1,2);assert not svc.handle_bark_event(0,datetime(2024,1,1,23));c.t=3;assert svc.handle_bark_event(3,datetime(2024,1,1,23));svc._play_thread.join()
def test_config_boundary_clears():
 c=Clock();svc=DogwatchService(Config(),Classifier(),Player(),c);svc.counter.events.append(1);svc.segmenter.onset=1;svc.update_config(Config());assert not svc.counter.events and svc.segmenter.onset is None
