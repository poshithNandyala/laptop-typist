import http.server
import socketserver
import os
import sys

PORT = 8000

# Serve from script directory
ui_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(ui_dir)

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress logging for silent mode

# Redirect stdout/stderr to null for pythonw compatibility
if sys.executable.endswith('pythonw.exe'):
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

# Bind to all interfaces for remote access
with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    httpd.serve_forever()
