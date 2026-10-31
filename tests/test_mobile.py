#!/usr/bin/env python3
"""
Unit and integration tests for AntiRoute Mobile Gateway & Smartphone API
"""

import os
import sys
import json
import unittest
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import proxy_manager as pm
import mobile_server


class TestMobileGateway(unittest.TestCase):
    def test_lan_ips_detection(self):
        ips = pm.get_lan_ips()
        self.assertIsInstance(ips, list)
        self.assertTrue(len(ips) > 0)
        label, ip = ips[0]
        self.assertIsInstance(label, str)
        self.assertIsInstance(ip, str)
        # Should be a valid IPv4
        parts = ip.split(".")
        self.assertEqual(len(parts), 4)

    def test_mobile_assets_exist(self):
        mobile_dir = BASE_DIR / "mobile"
        self.assertTrue((mobile_dir / "index.html").exists())
        self.assertTrue((mobile_dir / "setup.html").exists())
        self.assertTrue((mobile_dir / "manifest.json").exists())
        self.assertTrue((mobile_dir / "sw.js").exists())
        self.assertTrue((mobile_dir / "icon.svg").exists())

        # Check manifest is valid JSON
        manifest_data = json.loads((mobile_dir / "manifest.json").read_text())
        self.assertIn("name", manifest_data)
        self.assertIn("icons", manifest_data)

    def test_mobile_agent_connection_info(self):
        info = pm.get_agent_connection_info("mobile")
        self.assertIn("name", info)
        self.assertIn("env", info)
        self.assertIn("MOBILE_CHAT_URL", info["env"])
        self.assertIn("OPENAI_BASE_URL", info["env"])
        self.assertIn("sk-antigravity-claude", info["env"]["OPENAI_API_KEY"])
        self.assertIn("gemini-3.8-flash-high", info["env"]["DEFAULT_MODEL"])

    def test_mobile_server_status_endpoint(self):
        url = "http://127.0.0.1:8318/api/status"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            self.assertEqual(resp.status, 200)
            self.assertEqual(resp.headers.get("Content-Type"), "application/json")
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("status", data)
            self.assertIn("primary_ip", data)
            self.assertIn("mobile_chat_url", data)
            self.assertIn("api_endpoint", data)
            self.assertTrue(data.get("proxy_online"))

    def test_mobile_server_qr_endpoint(self):
        url = "http://127.0.0.1:8318/api/qr"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            self.assertEqual(resp.status, 200)
            self.assertEqual(resp.headers.get("Content-Type"), "image/png")
            content = resp.read()
            # PNG file magic bytes: \x89PNG\r\n\x1a\n
            self.assertTrue(content.startswith(b"\x89PNG\r\n\x1a\n"))

    def test_mobile_server_chat_page(self):
        url = "http://127.0.0.1:8318/"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            self.assertEqual(resp.status, 200)
            html = resp.read().decode("utf-8")
            self.assertIn("AntiRoute Gemini Mobile", html)
            self.assertIn("Voice Talk Mode", html)
            self.assertIn("gemini-3.8-flash-high", html)

    def test_mobile_proxy_models_endpoint(self):
        url = "http://127.0.0.1:8318/v1/models"
        req = urllib.request.Request(url, headers={"Authorization": "Bearer sk-antigravity-claude"})
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("data", data)
            model_ids = [m["id"] for m in data["data"]]
            self.assertIn("gemini-3.8-flash-high", model_ids)


if __name__ == "__main__":
    unittest.main()
