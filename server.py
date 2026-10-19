#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
server.py — Zero-Dependency B2B AI Sales Engine & Client Demo Sandbox Server
Built strictly with Python standard library. Runs 100% reliably on any machine without pip.
"""

import sys
import io
import os
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Ensure UTF-8 output on Windows
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from core.catalog_manager import CatalogManager
from core.ai_sales_brain import AISalesBrain

catalog_mgr = CatalogManager()
sales_brain = AISalesBrain()

STATIC_DIR = BASE_DIR / "static"

class SandboxRequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status: int = 200, content_type: str = "application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path

        # 1. Root: Serve Client Demo Sandbox UI
        if path == "/" or path == "/index.html":
            index_file = STATIC_DIR / "index.html"
            if index_file.exists():
                self._set_headers(200, "text/html")
                with open(index_file, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self._set_headers(404, "text/plain")
                self.wfile.write(b"index.html not found")
            return

        # 2. API: Stores Catalog
        if path == "/api/stores":
            stores = catalog_mgr.load_stores()
            self._set_headers(200)
            self.wfile.write(json.dumps({"stores": stores}, ensure_ascii=False).encode("utf-8"))
            return

        # 3. API: Live Orders
        if path == "/api/orders":
            orders = sales_brain.get_orders()
            self._set_headers(200)
            self.wfile.write(json.dumps({"orders": orders}, ensure_ascii=False).encode("utf-8"))
            return

        # Fallback 404
        self._set_headers(404, "text/plain")
        self.wfile.write(b"Not Found")

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            body = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            body = {}

        # 1. API: Process Chat Message
        if path == "/api/chat":
            store_id = body.get("store_id", "fashion_boutique")
            message = body.get("message", "")
            history = body.get("history", [])

            store = catalog_mgr.get_store(store_id)
            result = sales_brain.process_message(store, message, history)

            self._set_headers(200)
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            return

        # 2. API: Add Custom Client Store
        if path == "/api/stores/add":
            store_id = catalog_mgr.add_store(body)
            self._set_headers(200)
            self.wfile.write(json.dumps({"success": True, "store_id": store_id}).encode("utf-8"))
            return

        self._set_headers(404, "text/plain")
        self.wfile.write(b"Not Found")

    def log_message(self, format, *args):
        """Clean minimal terminal logs."""
        pass


def run_server(port: int = 5050):
    server_address = ("127.0.0.1", port)
    try:
        httpd = HTTPServer(server_address, SandboxRequestHandler)
    except OSError:
        # Fallback to alternative port if 5050 is busy
        port = 5055
        server_address = ("127.0.0.1", port)
        httpd = HTTPServer(server_address, SandboxRequestHandler)

    url = f"http://127.0.0.1:{port}"
    print("=" * 65)
    print("🚀 B2B AI SALES ENGINE & CLIENT DEMO SANDBOX LIVE!")
    print("=" * 65)
    print(f"🔗 Sandbox UI URL : {url}")
    print("⚡ Powered by   : Google Gemini + Multi-Tenant Core Architecture")
    print("📱 Client Demos  : Fashion, Gadget, Organic Food & Custom Shops")
    print("📦 Order Ledger  : Real-Time Synced in orders/orders.json")
    print("=" * 65)
    print("👉 Press Ctrl+C in terminal to stop.")
    print("=" * 65)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped.")
        httpd.server_close()


if __name__ == "__main__":
    port = 5050
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port)
