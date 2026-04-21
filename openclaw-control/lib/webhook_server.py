#!/usr/bin/env python3
import hmac
import hashlib
import json
import os
import subprocess
import tempfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def verify_signature(body: bytes, signature_header: str | None) -> bool:
    secret = os.environ.get("GITHUB_WEBHOOK_SECRET", "")
    if not secret:
        return os.environ.get("ALLOW_INSECURE_GITHUB_WEBHOOKS", "").lower() in {"1", "true", "yes", "on"}
    if not signature_header:
        return False
    expected = "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        expected_path = os.environ.get("CONTROL_WEBHOOK_PATH", "/hooks/github/projects-v2-item")
        if self.path != expected_path:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"status":"error","summary":"unknown path"}')
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        if not verify_signature(body, self.headers.get("X-Hub-Signature-256")):
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b'{"status":"error","summary":"invalid signature"}')
            return
        event = self.headers.get("X-GitHub-Event", "")
        with tempfile.TemporaryDirectory() as tmpdir:
            payload_path = Path(tmpdir) / "payload.json"
            payload_path.write_bytes(body)
            if event == "projects_v2_item":
                command = [
                    "bash",
                    str(ROOT / "scripts" / "oc-sdlc-from-github-webhook"),
                    str(payload_path),
                ]
            else:
                self.send_response(202)
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ignored", "event": event}).encode("utf-8"))
                return
            completed = subprocess.run(command, capture_output=True, text=True, env=os.environ.copy())
            self.send_response(200 if completed.returncode == 0 else 500)
            self.end_headers()
            output = completed.stdout.strip() or completed.stderr.strip() or '{"status":"error","summary":"empty"}'
            self.wfile.write(output.encode("utf-8"))

    def log_message(self, fmt, *args):
        return


def main():
    port = int(os.environ.get("CONTROL_WEBHOOK_PORT", "8787"))
    server = HTTPServer(("0.0.0.0", port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
