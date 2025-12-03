#!/usr/bin/env python3
"""
Simple HTTP server to serve the LLM Traceability Dashboard
"""

import http.server
import socketserver
import os
import sys
from urllib.parse import urlparse

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        # Suppress default server logs, keep only important ones
        if args and isinstance(args[0], str) and ("GET /" in args[0] or "POST /" in args[0]):
            return
        super().log_message(format, *args)

def main():
    PORT = 3001

    # Change to dashboard directory
    dashboard_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(dashboard_dir)

    Handler = CORSHTTPRequestHandler

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"""
🚀 LLM Traceability Dashboard Server Started!

📊 Dashboard URL: http://localhost:{PORT}
🔗 API Endpoint: http://localhost:8000
📖 API Docs: http://localhost:8000/docs

Features Available:
✅ Real-time Analytics Overview
✅ Model Performance Charts
✅ Session Search & Filtering
✅ Cost & Token Analysis
✅ Interactive Session Details
✅ Auto-refresh (30 seconds)

Press Ctrl+C to stop the server...
        """)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Dashboard server stopped!")
            sys.exit(0)

if __name__ == "__main__":
    main()