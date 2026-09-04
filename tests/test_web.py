from fastapi.testclient import TestClient
from config import Config
from service import DogwatchService
class C:
 def __call__(self):return 0
class P:
 def play(self,p):pass
class M:pass
def test_invalid_dashboard_update(tmp_path):
 from web.server import create_app
 app=create_app(DogwatchService(Config(response_path='sounds/response.wav'),M(),P(),C()),tmp_path/'config.json');client=TestClient(app)
 data=client.get('/api/config').json();data['required_barks']=0;r=client.put('/api/config',json=data);assert r.status_code==422 and 'required_barks' in r.json()['detail']
