#!/usr/bin/env python3
"""
AntiRoute Mobile Gateway & Companion Server
Provides a mobile-first Web Chat PWA and standard OpenAI/Anthropic API endpoint
accessible directly from smartphones on local Wi-Fi, Hotspot, and Tailscale networks.
"""

import os
import sys
import json
import time
import signal
import socket
import urllib.request
import urllib.error
import http.client
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import io

BASE_DIR = Path(__file__).resolve().parent
MOBILE_DIR = BASE_DIR / "mobile"
PID_PATH = BASE_DIR / "mobile.pid"
LOG_PATH = BASE_DIR / "mobile.log"

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8318
PROXY_HOST = "127.0.0.1"
PROXY_PORT = 8317
API_KEY = "sk-antigravity-claude"


def get_lan_ips() -> List[Tuple[str, str]]:
    """Detect LAN and interface IP addresses for smartphone connection."""
    ips = []
    # Primary default gateway route
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ips.append(("Wi-Fi / LAN", s.getsockname()[0]))
    except Exception:
        pass

    # Inspect network interfaces
    try:
        import subprocess
        res = subprocess.run(["hostname", "-I"], capture_output=True, text=True, timeout=2)
        for raw_ip in res.stdout.strip().split():
            ip = raw_ip.strip()
            if ip and not ip.startswith("127.") and ":" not in ip:
                if not any(ip == existing[1] for existing in ips):
                    label = "Hotspot / Network" if ip.startswith("192.168.43.") or ip.startswith("172.") else "Interface"
                    ips.append((label, ip))
    except Exception:
        pass

    if not ips:
        ips.append(("Local", "127.0.0.1"))
    return ips


def get_primary_ip() -> str:
    """Return the primary LAN IP or 127.0.0.1."""
    lan_ips = get_lan_ips()
    return lan_ips[0][1] if lan_ips else "127.0.0.1"


def print_ascii_qr(url: str):
    """Print ASCII QR Code directly to terminal for camera scanning."""
    try:
        import qrcode
        qr = qrcode.QRCode(box_size=1, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        print("\n" + "=" * 60)
        print(f" 📱 SCAN QR CODE WITH SMARTPHONE CAMERA TO CHAT:")
        print(f"    URL: {url}")
        print("=" * 60)
        qr.print_ascii(invert=True)
        print("=" * 60 + "\n")
    except Exception as e:
        print(f"(QR generator unavailable: {e})")


class MobileRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for AntiRoute Mobile Gateway."""

    server_version = "AntiRouteMobile/1.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):
        # Silence routine request logging unless needed for debug
        pass

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS, PATCH")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, x-api-key, anthropic-version")
        self.send_header("Access-Control-Expose-Headers", "*")

    def do_HEAD(self):
        """Handle HEAD requests similarly to GET without body."""
        self.do_GET()

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(204)
        self.send_cors_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        parsed_path = self.path.split("?")[0]

        # 1. Root and Web Chat SPA
        if parsed_path in ["/", "/chat", "/index.html"]:
            self.serve_file(MOBILE_DIR / "index.html", "text/html; charset=utf-8")
            return

        # 2. Setup Guide
        if parsed_path in ["/setup", "/setup.html", "/guide"]:
            self.serve_file(MOBILE_DIR / "setup.html", "text/html; charset=utf-8")
            return

        # 3. PWA Manifest & Service Worker
        if parsed_path == "/manifest.json":
            self.serve_file(MOBILE_DIR / "manifest.json", "application/manifest+json")
            return

        if parsed_path in ["/sw.js", "/service-worker.js"]:
            self.serve_file(MOBILE_DIR / "sw.js", "application/javascript")
            return

        # 4. App Icon
        if parsed_path == "/icon.svg":
            self.serve_file(MOBILE_DIR / "icon.svg", "image/svg+xml")
            return

        # 5. Status API
        if parsed_path == "/api/status":
            self.handle_api_status()
            return

        # 6. QR Code Image Generator API
        if parsed_path == "/api/qr":
            self.handle_api_qr()
            return

        # 7. Proxy API calls (/v1/...) to cli-proxy-api
        if parsed_path.startswith("/v1/"):
            self.proxy_request("GET")
            return

        # Not found fallback
        self.send_response(404)
        self.send_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"error": "Endpoint not found"}')

    def do_POST(self):
        parsed_path = self.path.split("?")[0]
        if parsed_path.startswith("/v1/"):
            self.proxy_request("POST")
            return

        self.send_response(404)
        self.send_cors_headers()
        self.end_headers()

    def serve_file(self, filepath: Path, content_type: str):
        if not filepath.exists():
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"File not found")
            return

        content = filepath.read_bytes()
        self.send_response(200)
        self.send_cors_headers()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(content)

    def handle_api_status(self):
        lan_ips = get_lan_ips()
        primary_ip = lan_ips[0][1] if lan_ips else "127.0.0.1"

        # Check cli-proxy-api health
        proxy_healthy = False
        models = []
        try:
            req = urllib.request.Request(f"http://{PROXY_HOST}:{PROXY_PORT}/v1/models", headers={"Authorization": f"Bearer {API_KEY}"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    proxy_healthy = True
                    data = json.loads(resp.read().decode("utf-8"))
                    models = [m.get("id") for m in data.get("data", [])]
        except Exception:
            pass

        info = {
            "status": "online" if proxy_healthy else "proxy_offline",
            "proxy_online": proxy_healthy,
            "primary_ip": primary_ip,
            "interfaces": lan_ips,
            "mobile_chat_url": f"http://{primary_ip}:{DEFAULT_PORT}",
            "mobile_setup_url": f"http://{primary_ip}:{DEFAULT_PORT}/setup",
            "api_endpoint": f"http://{primary_ip}:{DEFAULT_PORT}/v1",
            "direct_proxy_endpoint": f"http://{primary_ip}:{PROXY_PORT}/v1",
            "api_key": API_KEY,
            "models": models or ["gemini-3.8-flash-high", "gemini-3.1-pro-preview"],
            "server_time": time.time()
        }
        data = json.dumps(info, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def handle_api_qr(self):
        primary_ip = get_primary_ip()
        url = f"http://{primary_ip}:{DEFAULT_PORT}"
        try:
            import qrcode
            qr = qrcode.QRCode(version=1, box_size=8, border=2)
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="#090d16", back_color="#ffffff")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            png_bytes = buf.getvalue()

            self.send_response(200)
            self.send_cors_headers()
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(png_bytes)))
            self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()
            self.wfile.write(png_bytes)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"QR Error: {e}".encode())

    def proxy_request(self, method: str):
        """Proxy incoming request to cli-proxy-api with real-time SSE streaming support."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        # Build forward headers
        forward_headers = {}
        for key, val in self.headers.items():
            k_low = key.lower()
            if k_low not in ["host", "content-length", "connection"]:
                forward_headers[key] = val

        # Ensure authorization header is forwarded or default applied
        if "authorization" not in [k.lower() for k in forward_headers]:
            forward_headers["Authorization"] = f"Bearer {API_KEY}"

        forward_headers["Host"] = f"{PROXY_HOST}:{PROXY_PORT}"

        conn = None
        try:
            conn = http.client.HTTPConnection(PROXY_HOST, PROXY_PORT, timeout=60)
            conn.request(method, self.path, body=body, headers=forward_headers)
            resp = conn.getresponse()

            # Send status code
            self.send_response(resp.status)
            self.close_connection = True

            # Send response headers
            is_event_stream = False
            for k, v in resp.getheaders():
                k_low = k.lower()
                if k_low == "content-type" and "text/event-stream" in v:
                    is_event_stream = True
                if k_low not in ["connection", "transfer-encoding", "access-control-allow-origin", "access-control-allow-headers"]:
                    self.send_header(k, v)

            self.send_header("Connection", "close")
            self.send_cors_headers()
            self.end_headers()

            # Stream body to client
            while True:
                chunk = resp.read(1024)
                if not chunk:
                    break
                self.wfile.write(chunk)
                if is_event_stream:
                    self.wfile.flush()
                    if b"data: [DONE]" in chunk or b"message_stop" in chunk:
                        break

            self.wfile.flush()
            try:
                self.connection.shutdown(socket.SHUT_WR)
            except Exception:
                pass

        except Exception as e:
            try:
                self.send_response(502)
                self.send_cors_headers()
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                err = json.dumps({"error": f"AntiRoute Mobile Gateway Proxy Error: {e}"}).encode()
                self.wfile.write(err)
            except Exception:
                pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


def get_mobile_pid() -> Optional[int]:
    """Return PID if mobile server process is running, else None."""
    if PID_PATH.exists():
        try:
            pid = int(PID_PATH.read_text().strip())
            os.kill(pid, 0)
            return pid
        except (ValueError, OSError):
            pass

    try:
        import subprocess
        res = subprocess.run(["pgrep", "-f", "mobile_server.py.*--serve"], capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            pids = [int(p) for p in res.stdout.strip().splitlines() if p.isdigit()]
            if pids:
                return pids[0]
    except Exception:
        pass
    return None


def run_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    """Start the multi-threaded HTTP mobile gateway."""
    PID_PATH.write_text(str(os.getpid()))

    def handle_signal(sig, frame):
        print("\nShutting down Mobile Gateway...")
        if PID_PATH.exists():
            PID_PATH.unlink(missing_ok=True)
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    primary_ip = get_primary_ip()
    mobile_url = f"http://{primary_ip}:{port}"

    print("==================================================================")
    print(" ✦ AntiRoute Mobile Gateway & Web Chat Cockpit ✦")
    print("==================================================================")
    print(f"• Listening on:        http://{host}:{port}")
    print(f"• Smartphone Web Chat: {mobile_url}")
    print(f"• Smartphone Setup:    {mobile_url}/setup")
    print(f"• Mobile OpenAI API:   {mobile_url}/v1")
    print(f"• Direct Proxy API:    http://{primary_ip}:{PROXY_PORT}/v1")
    print(f"• API Key:             {API_KEY}")
    print("==================================================================")

    print_ascii_qr(mobile_url)

    server = ThreadingHTTPServer((host, port), MobileRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        if PID_PATH.exists():
            PID_PATH.unlink(missing_ok=True)


def start_daemon(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> Tuple[bool, str]:
    """Start mobile server in background daemon mode."""
    existing_pid = get_mobile_pid()
    if existing_pid:
        primary_ip = get_primary_ip()
        return True, f"Mobile Gateway is already running (PID {existing_pid}) at http://{primary_ip}:{port}"

    import subprocess
    cmd = [sys.executable, str(Path(__file__).resolve()), "--serve", "--host", host, "--port", str(port)]
    with open(LOG_PATH, "a") as log_f:
        proc = subprocess.Popen(cmd, stdout=log_f, stderr=log_f, start_new_session=True)

    time.sleep(1)
    if proc.poll() is None:
        PID_PATH.write_text(str(proc.pid))
        primary_ip = get_primary_ip()
        return True, f"Mobile Gateway successfully started (PID {proc.pid}) at http://{primary_ip}:{port}"
    else:
        return False, f"Failed to start Mobile Gateway. Check {LOG_PATH}"


def stop_daemon() -> Tuple[bool, str]:
    """Stop running mobile server daemon."""
    pid = get_mobile_pid()
    if not pid:
        return True, "Mobile Gateway is not running."

    try:
        os.kill(pid, signal.SIGTERM)
        for _ in range(15):
            time.sleep(0.2)
            try:
                os.kill(pid, 0)
            except OSError:
                PID_PATH.unlink(missing_ok=True)
                return True, f"Mobile Gateway (PID {pid}) stopped."
        # Force kill if still alive
        os.kill(pid, signal.SIGKILL)
        PID_PATH.unlink(missing_ok=True)
        return True, f"Mobile Gateway (PID {pid}) forcibly terminated."
    except Exception as e:
        PID_PATH.unlink(missing_ok=True)
        return False, f"Error stopping Mobile Gateway: {e}"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AntiRoute Mobile Gateway & Web Chat")
    parser.add_argument("--serve", action="store_true", help="Run the server loop")
    parser.add_argument("--start", action="store_true", help="Start daemon in background")
    parser.add_argument("--stop", action="store_true", help="Stop background daemon")
    parser.add_argument("--status", action="store_true", help="Check gateway status")
    parser.add_argument("--qr", action="store_true", help="Print terminal ASCII QR Code")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host interface to bind")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to listen on")

    args = parser.parse_args()

    if args.stop:
        ok, msg = stop_daemon()
        print(msg)
        sys.exit(0 if ok else 1)

    if args.status:
        pid = get_mobile_pid()
        primary_ip = get_primary_ip()
        if pid:
            print(f"Mobile Gateway: RUNNING (PID {pid})")
            print(f"URL:            http://{primary_ip}:{args.port}")
        else:
            print("Mobile Gateway: STOPPED")
        sys.exit(0)

    if args.qr:
        primary_ip = get_primary_ip()
        print_ascii_qr(f"http://{primary_ip}:{args.port}")
        sys.exit(0)

    if args.start:
        ok, msg = start_daemon(host=args.host, port=args.port)
        print(msg)
        if ok:
            primary_ip = get_primary_ip()
            print_ascii_qr(f"http://{primary_ip}:{args.port}")
        sys.exit(0 if ok else 1)

    # Default: Run foreground server
    run_server(host=args.host, port=args.port)
