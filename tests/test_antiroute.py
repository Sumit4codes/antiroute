#!/usr/bin/env python3
"""
Unit and integration tests for AntiRoute
"""

import os
import sys
import json
import shutil
import tempfile
import unittest
import subprocess
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import proxy_manager as pm
import tui


class TestProxyManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="antiroute_test_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_load_config(self):
        config = pm.load_config()
        self.assertIn("host", config)
        self.assertIn("port", config)
        self.assertIn("api_keys", config)
        self.assertEqual(config["port"], 8317)
        self.assertIn("sk-antigravity-claude", config["api_keys"])

    def test_agent_connection_info(self):
        tools = ["hermes", "opencode", "claude", "aider", "goose", "droid"]
        for tool in tools:
            info = pm.get_agent_connection_info(tool)
            self.assertIn("name", info)
            self.assertIn("env", info)
            self.assertIn("snippet", info)
            self.assertIn("description", info)
            self.assertTrue(len(info["name"]) > 0)

    def test_export_agent_env(self):
        target = self.test_dir / ".env.test_hermes"
        exported_path = pm.export_agent_env("hermes", target_file=str(target))
        self.assertTrue(Path(exported_path).exists())
        content = Path(exported_path).read_text()
        self.assertIn("OPENAI_BASE_URL", content)
        self.assertIn("sk-antigravity-claude", content)

    def test_configure_opencode(self):
        ok, msg = pm.configure_opencode(set_default=True, local_dir=self.test_dir)
        self.assertTrue(ok)
        opencode_json = self.test_dir / "opencode.json"
        self.assertTrue(opencode_json.exists())
        data = json.loads(opencode_json.read_text())
        self.assertIn("provider", data)
        self.assertIn("antigravity", data["provider"])
        self.assertEqual(data["provider"]["antigravity"]["options"]["apiKey"], "sk-antigravity-claude")
        self.assertEqual(data["model"], "antigravity/gemini-3.8-flash-high")

    def test_configure_hermes(self):
        ok, msg = pm.configure_hermes(set_default=True, hermes_dir=self.test_dir)
        self.assertTrue(ok)
        hermes_yaml = self.test_dir / "config.yaml"
        self.assertTrue(hermes_yaml.exists())
        content = hermes_yaml.read_text()
        self.assertIn("antiroute", content)
        self.assertIn("gemini-3.8-flash-high", content)


class TestTUIRender(unittest.TestCase):
    class MockWindow:
        def __init__(self, y=32, x=105):
            self.max_y = y
            self.max_x = x
        def getmaxyx(self):
            return (self.max_y, self.max_x)
        def erase(self): pass
        def clear(self): pass
        def refresh(self): pass
        def nodelay(self, b): pass
        def addstr(self, y, x, s, attr=0):
            assert y < self.max_y and x < self.max_x, f"Out of bounds: y={y}, x={x}"

    def test_render_all_tabs(self):
        mock_win = self.MockWindow()
        app = tui.TUIApp(mock_win)

        for tab_idx in range(len(tui.TABS)):
            app.current_tab = tab_idx
            app.render()

    def test_render_all_agent_profiles(self):
        mock_win = self.MockWindow()
        app = tui.TUIApp(mock_win)
        app.current_tab = 1  # Agent Connect Hub

        for agent_idx in range(len(tui.AGENT_TOOLS)):
            app.agent_selected_idx = agent_idx
            app.render()


class TestCLICommands(unittest.TestCase):
    def test_cli_status(self):
        res = subprocess.run([sys.executable, str(BASE_DIR / "tui.py"), "status"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("AntiRoute", res.stdout)
        self.assertIn("Service Status", res.stdout)

    def test_cli_connect_overview(self):
        res = subprocess.run([sys.executable, str(BASE_DIR / "tui.py"), "connect"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("Hermes", res.stdout)
        self.assertIn("OpenCode", res.stdout)

    def test_cli_connect_tool(self):
        res = subprocess.run([sys.executable, str(BASE_DIR / "tui.py"), "connect", "hermes"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("OPENAI_BASE_URL", res.stdout)


if __name__ == "__main__":
    unittest.main()
