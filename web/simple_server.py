from __future__ import annotations

from dataclasses import asdict
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

from config import Config, ConfigError, save_config

MAX_BODY_BYTES = 64 * 1024


def make_server(service, config_path="config.json", host="127.0.0.1", port=8765):
    root = Path(__file__).parent

    class Handler(BaseHTTPRequestHandler):
        server_version = "DogwatchHTTP/1.0"

        def log_message(self, fmt, *args):
            return

        def parse_request(self):
            if not super().parse_request():
                return False
            if not self._from_dashboard():
                self._empty(403)
                return False
            return True

        def _from_dashboard(self):
            # Binding to 127.0.0.1 keeps the network out, but not websites open in a local
            # browser: a foreign Host means DNS rebinding, a foreign Origin means CSRF.
            port = self.server.server_address[1]
            hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
            origin = self.headers.get("origin")
            return self.headers.get("host", "").lower() in hosts and (
                origin is None or origin.lower() in {f"http://{h}" for h in hosts}
            )

        def _json(self, status, payload):
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _empty(self, status=204):
            self.send_response(status)
            self.send_header("content-length", "0")
            self.end_headers()

        def _read_json(self):
            try:
                length = int(self.headers.get("content-length", "0") or "0")
            except ValueError as exc:
                raise ConfigError("invalid content-length") from exc
            if not 0 <= length <= MAX_BODY_BYTES:
                raise ConfigError("request body too large")
            if length == 0:
                return {}
            try:
                return json.loads(self.rfile.read(length).decode("utf-8"))
            except json.JSONDecodeError as exc:
                raise ConfigError(f"invalid JSON: {exc.msg}") from exc

        def _file(self, path):
            try:
                resolved = path.resolve()
                web_root = root.resolve()
                if web_root not in resolved.parents and resolved != web_root:
                    self._empty(404)
                    return
                data = resolved.read_bytes()
            except OSError:
                self._empty(404)
                return
            content_type = mimetypes.guess_type(str(resolved))[0] or "application/octet-stream"
            self.send_response(200)
            self.send_header("content-type", content_type)
            self.send_header("content-length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            path = unquote(self.path.split("?", 1)[0])
            if path == "/":
                self._file(root / "index.html")
            elif path == "/favicon.ico":
                self._empty()
            elif path == "/api/status":
                self._json(200, service.status())
            elif path == "/api/config":
                self._json(200, asdict(service.config))
            elif path.startswith("/static/"):
                self._file(root / path.removeprefix("/static/"))
            else:
                self._empty(404)

        def do_PUT(self):
            if self.path.split("?", 1)[0] != "/api/config":
                self._empty(404)
                return
            try:
                cfg = Config.from_dict(self._read_json(), Path(config_path).parent)
                save_config(cfg, config_path)
                service.update_config(cfg)
                self._json(200, asdict(cfg))
            except ConfigError as exc:
                self._json(422, {"detail": str(exc)})

        def do_POST(self):
            path = self.path.split("?", 1)[0]
            if path.startswith("/api/simulate/"):
                try:
                    count = int(path.rsplit("/", 1)[1])
                except ValueError:
                    self._json(400, {"detail": "count must be 1 or 5"})
                    return
                if count not in (1, 5):
                    self._json(400, {"detail": "count must be 1 or 5"})
                    return
                accepted = 0
                base = service.clock()
                for i in range(count):
                    accepted += int(service.handle_bark_event(base + i * .01))
                self._json(200, {"accepted": accepted, "status": service.status()})
                return
            if path in ("/api/browser-detection", "/api/browser-preview"):
                try:
                    data = self._read_json()
                    score = float(data.get("score", 0))
                    if not 0 <= score <= 1:
                        raise ValueError
                except (ConfigError, TypeError, ValueError):
                    self._json(422, {"detail": "score must be a number between 0 and 1"})
                    return
                dog_scores = data.get("dog_scores", {})
                top_predictions = data.get("top_predictions", [])
                if isinstance(dog_scores, dict):
                    service.last_dog_scores = {str(k): float(v) for k, v in dog_scores.items() if isinstance(v, (int, float))}
                if isinstance(top_predictions, list):
                    service.last_top_predictions = top_predictions[:10]
                service.last_model_score = score
                service.last_score = max(service.last_acoustic_score, score)
                if path == "/api/browser-detection":
                    accepted = service.handle_bark_event()
                    self._json(200, {"accepted": accepted, "status": service.status()})
                else:
                    self._json(200, service.status())
                return
            if path == "/api/test-response":
                if not service.test_response():
                    self._json(409, {"detail": "response is disabled or already suppressed"})
                    return
                self._json(200, service.status())
                return
            self._empty(404)

    return ThreadingHTTPServer((host, port), Handler)


def serve(service, config_path="config.json", host="127.0.0.1", port=8765):
    httpd = make_server(service, config_path, host, port)
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
