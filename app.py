#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,logging,signal,sys,threading,time
from pathlib import Path
from config import ConfigError,load_config

class JsonFormatter(logging.Formatter):
 def format(self,record):
  data={"time":self.formatTime(record,"%Y-%m-%dT%H:%M:%S%z"),"level":record.levelname,"logger":record.name,"message":record.getMessage()}
  for key in ("path","device","sample_rate","detail","dbfs"):
   if hasattr(record,key):data[key]=getattr(record,key)
  if record.exc_info:data["exception"]=self.formatException(record.exc_info)
  return json.dumps(data)
def logging_setup(debug=False):
 h=logging.StreamHandler();h.setFormatter(JsonFormatter());logging.basicConfig(level=logging.DEBUG if debug else logging.INFO,handlers=[h],force=True)
def validate_startup(config):
 p=Path(config.response_path)
 if not p.is_absolute():p=Path(__file__).parent/p
 if not p.is_file():raise ConfigError(f"response file not found: {p}; see sounds/README.md")
def main(argv=None):
 parser=argparse.ArgumentParser(description="Local YAMNet dog-bark monitor");parser.add_argument("--config",default="config.json");m=parser.add_mutually_exclusive_group();m.add_argument("--calibrate",action="store_true");m.add_argument("--debug",action="store_true");args=parser.parse_args(argv);logging_setup(args.debug)
 try:cfg=load_config(args.config);validate_startup(cfg)
 except ConfigError as exc:logging.error("startup_validation_failed",extra={"detail":str(exc)});return 2
 try:
  from audio.capture import AudioCapture
  if args.calibrate:
   from audio.processing import rms_dbfs
   cap=AudioCapture();cap.start();logging.info("calibration_started (Ctrl-C to stop; values are dBFS, not SPL)")
   try:
    while True:
     block=cap.read();
     if block is not None:logging.info("calibration_level",extra={"dbfs":rms_dbfs(block)[1]})
   except KeyboardInterrupt:pass
   finally:cap.stop()
   return 0
  from ml.yamnet_classifier import YAMNetClassifier
  from audio.playback import MacOSAudioPlayer
  from service import DogwatchService
  classifier=YAMNetClassifier();service=DogwatchService(cfg,classifier,MacOSAudioPlayer());capture=AudioCapture();capture.start();stop=threading.Event()
  def consume():
   while not stop.is_set():
    block=capture.read(.5)
    if block is not None:service.process_audio(block,capture.sample_rate)
  worker=threading.Thread(target=consume,name="audio",daemon=True);worker.start()
  import uvicorn
  from web.server import create_app
  server=uvicorn.Server(uvicorn.Config(create_app(service,args.config),host="127.0.0.1",port=8765,log_config=None))
  def shutdown(*_):logging.info("shutdown_requested");stop.set();server.should_exit=True
  signal.signal(signal.SIGINT,shutdown);signal.signal(signal.SIGTERM,shutdown);server.run();stop.set();capture.stop();worker.join(2);return 0
 except Exception:logging.exception("fatal_startup_or_runtime_error");return 1
if __name__=="__main__":raise SystemExit(main())
