#!/usr/bin/env python3
"""
Local HTTP server for Parlance fine-tuned SLMs.

Used by the Parlance web journal and iOS app (via native bridge).

  python parlance_slm_server.py
  # → http://127.0.0.1:8765/health
  # → POST http://127.0.0.1:8765/analyze  {"sentence","language","level"}
"""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

TRAINING_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TRAINING_DIR))

from parlance_slm_infer import get_engine, is_model_ready  # noqa: E402

HOST = "127.0.0.1"
PORT = 8765


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[slm] {self.address_string()} — {fmt % args}")

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code: int, body: dict):
        payload = json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self._cors()
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            self._json(200, {
                "ok": True,
                "service": "parlance-slm",
                "spanish_ready": is_model_ready("es"),
                "french_ready": is_model_ready("fr"),
            })
            return
        self._json(404, {"error": "not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/analyze":
            self._json(404, {"error": "not found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError:
            self._json(400, {"error": "invalid JSON"})
            return

        sentence = (body.get("sentence") or "").strip()
        language = (body.get("language") or "es").lower()
        level = (body.get("level") or "").upper()
        rag_context = body.get("ragContext") or body.get("rag_context") or ""

        if not sentence:
            self._json(400, {"error": "sentence required"})
            return
        if language not in ("es", "fr"):
            self._json(400, {"error": "language must be es or fr"})
            return
        if not is_model_ready(language):
            self._json(503, {
                "error": f"Parlance {language} model not ready. Spanish is available; French pending Colab GPU."
                if language == "fr"
                else f"Spanish model missing or invalid under training/models/parlance-{language}/"
            })
            return

        try:
            engine = get_engine(language)
            feedback = engine.analyze(sentence, level=level, rag_context=rag_context)
            self._json(200, {"feedback": feedback, "source": f"Parlance SLM ({language})"})
        except FileNotFoundError as e:
            self._json(503, {"error": str(e)})
        except Exception as e:
            self._json(500, {"error": str(e)})


def main():
    print(f"Parlance SLM server → http://{HOST}:{PORT}")
    print("  GET  /health")
    print("  POST /analyze  {sentence, language, level}")
    print("Press Ctrl+C to stop.\n")
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()


if __name__ == "__main__":
    main()
