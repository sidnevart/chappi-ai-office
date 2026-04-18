#!/usr/bin/env python3
"""
Read-only HTTP file server for AI Office.
Exposes ~/Documents/Projects over HTTP (GET only).
Agent on VPS can fetch files via: curl http://<ngrok-url>/path/to/file
"""
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import urllib.parse

ROOT = Path.home() / "Documents" / "Projects"
PORT = 18500
TOKEN = os.environ.get("MAC_FILESERVER_TOKEN", "")

class ReadOnlyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Auth check
        if TOKEN:
            auth = self.headers.get("X-Token", "")
            if auth != TOKEN:
                self.send_response(401)
                self.end_headers()
                self.wfile.write(b"Unauthorized")
                return

        path = urllib.parse.unquote(self.path.lstrip("/"))
        target = ROOT / path

        # Safety: no path traversal
        try:
            target.resolve().relative_to(ROOT.resolve())
        except ValueError:
            self.send_response(403)
            self.end_headers()
            return

        if target.is_dir():
            # Return directory listing as text
            entries = sorted(target.iterdir())
            body = "\n".join(
                ("DIR  " if e.is_dir() else "FILE ") + e.name
                for e in entries
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(body)
        elif target.is_file():
            content = target.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt, *args):
        print(f"[fileserver] {self.address_string()} - {fmt % args}")

if __name__ == "__main__":
    print(f"Serving {ROOT} on port {PORT}")
    print(f"Auth token: {'set' if TOKEN else 'NONE (open!)'}")
    HTTPServer(("127.0.0.1", PORT), ReadOnlyHandler).serve_forever()
