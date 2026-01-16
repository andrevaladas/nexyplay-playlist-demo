#!/usr/bin/env python3
"""
Small helper to serve the playlist files over HTTP for local testing.

Usage:
  python3 serve_playlists.py            # serve current directory on port 8000
  python3 serve_playlists.py --port 9000 --dir /path/to/folder
"""

import argparse
import http.server
import socketserver
import socket
from pathlib import Path


class CorsRequestHandler(http.server.SimpleHTTPRequestHandler):
  """Adds permissive CORS headers so the app can fetch playlists."""

  def end_headers(self):
    self.send_header("Access-Control-Allow-Origin", "*")
    self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
    self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-Type")
    super().end_headers()

  def log_message(self, format, *args):
    # Less noisy logging
    print(self.log_date_time_string(), format % args)


def main():
  parser = argparse.ArgumentParser(description="Serve playlists over HTTP.")
  parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
  parser.add_argument("--dir", type=str, default=".", help="Directory to serve (default: current dir)")
  parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
  args = parser.parse_args()

  root = Path(args.dir).resolve()
  if not root.exists():
    raise SystemExit(f"Directory not found: {root}")

  handler = lambda *hargs, **hkw: CorsRequestHandler(*hargs, directory=str(root), **hkw)

  def _local_ips():
    ips = set()
    try:
      hostname = socket.gethostname()
      _, _, addrs = socket.gethostbyname_ex(hostname)
      for ip in addrs:
        if not ip.startswith("127."):
          ips.add(ip)
    except Exception:
      pass

    # UDP socket trick to discover the active LAN IP (no packets sent).
    try:
      with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        if ip and not ip.startswith("127."):
          ips.add(ip)
    except Exception:
      pass

    return sorted(ips)

  with socketserver.TCPServer((args.host, args.port), handler) as httpd:
    print(f"Serving {root} at http://{args.host}:{args.port}/")
    ips = _local_ips()
    if ips:
      print("Local network URLs:")
      for ip in ips:
        print(f"  http://{ip}:{args.port}/")
    print("Press Ctrl+C to stop.")
    try:
      httpd.serve_forever()
    except KeyboardInterrupt:
      print("\nShutting down...")


if __name__ == "__main__":
  main()
