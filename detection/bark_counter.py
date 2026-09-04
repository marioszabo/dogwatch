from collections import deque
class BarkCounter:
    def __init__(self,window_s:float,required_count:int): self.window_s=window_s; self.required_count=required_count; self.events=deque()
    def clear(self): self.events.clear()
    def add(self,timestamp:float)->bool:
        self.prune(timestamp); self.events.append(timestamp); return len(self.events)>=self.required_count
    def prune(self,now:float):
        while self.events and now-self.events[0]>self.window_s:self.events.popleft()
    def count(self,now:float)->int:self.prune(now); return len(self.events)
