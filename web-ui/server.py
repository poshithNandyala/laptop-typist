import http.server
import socketserver
import os

PORT = 8000

# Serve from script directory
ui_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(ui_dir)

class Handler(http.server.SimpleHTTPRequestHandler):
    pass

print(f"Web UI running at http://localhost:{PORT}")

# IMPORTANT: bind only to localhost
with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
    httpd.serve_forever()
