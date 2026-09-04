from datetime import datetime
from scheduler import is_quiet_time
def d(h,m):return datetime(2024,1,1,h,m)
def test_midnight_boundaries():
 assert is_quiet_time(d(22,30),'22:30','07:00');assert is_quiet_time(d(6,59),'22:30','07:00');assert not is_quiet_time(d(7,0),'22:30','07:00');assert not is_quiet_time(d(22,29),'22:30','07:00')
def test_same_day():
 assert is_quiet_time(d(10,0),'09:00','17:00');assert not is_quiet_time(d(17,0),'09:00','17:00')
