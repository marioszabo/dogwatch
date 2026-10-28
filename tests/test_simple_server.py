import http.client,threading
import pytest
from config import Config
from service import DogwatchService
from web.simple_server import make_server
class C:
 def __call__(self):return 0
class P:
 def play(self,p):pass
class M:pass
@pytest.fixture
def server(tmp_path):
 httpd=make_server(DogwatchService(Config(response_path='sounds/response.wav'),M(),P(),C()),tmp_path/'config.json',port=0)
 threading.Thread(target=httpd.serve_forever,daemon=True).start()
 yield httpd.server_address[1]
 httpd.shutdown();httpd.server_close()
def request(port,method,path,headers=None,body=None):
 conn=http.client.HTTPConnection('127.0.0.1',port,timeout=5)
 try:conn.request(method,path,body=body,headers=headers or {});r=conn.getresponse();r.read();return r.status
 finally:conn.close()
def test_dashboard_requests_are_served(server):
 assert request(server,'GET','/api/status')==200
 assert request(server,'GET','/api/status',{'Host':f'localhost:{server}'})==200
 assert request(server,'POST','/api/simulate/1',{'Origin':f'http://127.0.0.1:{server}'})==200
def test_dns_rebinding_host_is_rejected(server):
 assert request(server,'GET','/api/config',{'Host':f'attacker.example:{server}'})==403
 assert request(server,'PUT','/api/config',{'Host':f'attacker.example:{server}'},b'{}')==403
def test_cross_site_origin_is_rejected(server):
 for path in ('/api/test-response','/api/simulate/5','/api/browser-detection'):
  assert request(server,'POST',path,{'Origin':'https://attacker.example','Content-Type':'text/plain'},b'{"score":1}')==403
 assert request(server,'POST','/api/test-response',{'Origin':'null'})==403
def test_oversized_body_is_rejected(server):
 assert request(server,'POST','/api/browser-preview',{'Content-Length':str(10**9)})==422
