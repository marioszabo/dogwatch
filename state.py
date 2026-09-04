from enum import Enum
import threading,time
class State(str,Enum): DISABLED="DISABLED"; LISTENING="LISTENING"; COUNTING="COUNTING"; PLAYING="PLAYING"; COOLDOWN="COOLDOWN"
class StateMachine:
    def __init__(self,enabled=True,clock=time.monotonic): self._clock=clock; self._lock=threading.RLock(); self.state=State.LISTENING if enabled else State.DISABLED; self.suppressed_until=0.0
    def set_enabled(self,enabled:bool):
        with self._lock:self.state=State.LISTENING if enabled else State.DISABLED; self.suppressed_until=0
    def accepts_bark(self)->bool:
        with self._lock:self.tick(); return self.state in (State.LISTENING,State.COUNTING)
    def bark_counted(self):
        with self._lock:
            if not self.accepts_bark(): return False
            self.state=State.COUNTING; return True
    def playback_started(self):
        with self._lock:
            if self.state==State.DISABLED:return False
            self.state=State.PLAYING; return True
    def playback_finished(self,post_suppression:float,cooldown:float):
        with self._lock:self.state=State.COOLDOWN; self.suppressed_until=self._clock()+post_suppression+cooldown
    def tick(self):
        with self._lock:
            if self.state==State.COOLDOWN and self._clock()>=self.suppressed_until:self.state=State.LISTENING
        return self.state
