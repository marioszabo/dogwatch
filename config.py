"""Validated application configuration and safe persistence."""
from __future__ import annotations
from dataclasses import asdict, dataclass, fields
from datetime import datetime
import json, math, os, tempfile
from pathlib import Path
from typing import Any

class ConfigError(ValueError):
    """A configuration value is malformed or unsafe."""

def _time(value: str) -> str:
    try: datetime.strptime(value, "%H:%M")
    except (TypeError, ValueError) as exc: raise ConfigError(f"must be a 24-hour HH:MM time, got {value!r}") from exc
    return value

def _num(name: str, value: Any, low: float, high: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value): raise ConfigError(f"{name} must be a finite number")
    if not low <= value <= high: raise ConfigError(f"{name} must be between {low} and {high}")
    return float(value)

@dataclass(frozen=True)
class Config:
    enabled: bool = True
    quiet_start: str = "22:30"
    quiet_end: str = "07:00"
    bark_on_threshold: float = .45
    bark_off_threshold: float = .25
    min_event_duration_s: float = .20
    release_duration_s: float = .35
    min_event_gap_s: float = .50
    rolling_window_s: float = 30.0
    required_barks: int = 5
    post_playback_suppression_s: float = 1.0
    cooldown_s: float = 60.0
    response_path: str = "sounds/response.wav"
    rms_gate_dbfs: float | None = -55.0

    def validate(self, base_dir: Path | None = None) -> "Config":
        if type(self.enabled) is not bool: raise ConfigError("enabled must be a boolean")
        _time(self.quiet_start); _time(self.quiet_end)
        on=_num("bark_on_threshold",self.bark_on_threshold,0,1); off=_num("bark_off_threshold",self.bark_off_threshold,0,1)
        if off >= on: raise ConfigError("bark_off_threshold must be lower than bark_on_threshold")
        for n,lo,hi in [("min_event_duration_s",.01,30),("release_duration_s",.01,30),("min_event_gap_s",0,300),("rolling_window_s",.1,3600),("post_playback_suppression_s",0,300),("cooldown_s",0,86400)]: _num(n,getattr(self,n),lo,hi)
        if type(self.required_barks) is not int or not 1 <= self.required_barks <= 100: raise ConfigError("required_barks must be an integer between 1 and 100")
        if self.rms_gate_dbfs is not None: _num("rms_gate_dbfs",self.rms_gate_dbfs,-160,0)
        if not isinstance(self.response_path,str) or not self.response_path.strip(): raise ConfigError("response_path must be a non-empty path")
        path=Path(self.response_path).expanduser()
        if "\x00" in self.response_path: raise ConfigError("response_path contains an invalid NUL byte")
        if base_dir and not path.is_absolute():
            root=base_dir.resolve(); resolved=(root/path).resolve()
            if root not in resolved.parents and resolved != root: raise ConfigError("relative response_path must remain inside the application directory")
        return self

    @classmethod
    def from_dict(cls, data: dict[str,Any], base_dir: Path|None=None) -> "Config":
        if not isinstance(data,dict): raise ConfigError("configuration must be a JSON object")
        valid={f.name for f in fields(cls)}; unknown=set(data)-valid
        if unknown: raise ConfigError("unknown configuration field(s): "+", ".join(sorted(unknown)))
        try: return cls(**data).validate(base_dir)
        except TypeError as exc: raise ConfigError(str(exc)) from exc

def load_config(path: str|Path="config.json") -> Config:
    p=Path(path)
    try: data=json.loads(p.read_text())
    except FileNotFoundError as exc: raise ConfigError(f"configuration file not found: {p}") from exc
    except json.JSONDecodeError as exc: raise ConfigError(f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc
    return Config.from_dict(data,p.parent)

def save_config(config: Config,path: str|Path="config.json") -> None:
    p=Path(path); config.validate(p.parent); p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=p.name,dir=p.parent,text=True)
    try:
        with os.fdopen(fd,"w") as f: json.dump(asdict(config),f,indent=2); f.write("\n"); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,p)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
