from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
from fastapi import FastAPI,HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from config import Config,ConfigError,save_config

def create_app(service,config_path="config.json"):
 app=FastAPI(title="Dogwatch",docs_url=None,redoc_url=None); root=Path(__file__).parent
 app.mount("/static",StaticFiles(directory=root),name="static")
 @app.get("/")
 def index():return FileResponse(root/"index.html")
 @app.get("/api/status")
 def status():return service.status()
 @app.get("/api/config")
 def get_config():return asdict(service.config)
 @app.put("/api/config")
 def update(data:dict):
  try: cfg=Config.from_dict(data,Path(config_path).parent); save_config(cfg,config_path); service.update_config(cfg); return asdict(cfg)
  except ConfigError as exc:raise HTTPException(422,detail=str(exc))
 @app.post("/api/simulate/{count}")
 def simulate(count:int):
  if count not in (1,5):raise HTTPException(400,"count must be 1 or 5")
  accepted=0; base=service.clock()
  for i in range(count): accepted+=int(service.handle_bark_event(base+i*.01))
  return {"accepted":accepted,"status":service.status()}
 @app.post("/api/test-response")
 def test_response():
  if not service.test_response():raise HTTPException(409,"response is disabled or already suppressed")
  return service.status()
 return app
