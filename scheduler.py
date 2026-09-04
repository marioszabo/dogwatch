"""Quiet-hour schedule helpers; end times are exclusive."""
from datetime import datetime, time

def _parse(value: str) -> time: return datetime.strptime(value,"%H:%M").time()
def is_quiet_time(now: datetime, start: str, end: str) -> bool:
    current=now.time().replace(second=0,microsecond=0); a,b=_parse(start),_parse(end)
    if a == b: return True
    return a <= current < b if a < b else current >= a or current < b
