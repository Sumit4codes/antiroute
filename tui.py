#!/usr/bin/env python3
"""
AntiRoute - Antigravity AI Agent Router & TUI
Interactive terminal manager & router for Google Antigravity Gemini and AI agents (Hermes, OpenCode, Claude Code, Aider, etc.)
"""

import os
import sys
import time
import curses
import argparse
import subprocess
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional

import proxy_manager as pm

VERSION = "1.0.0"

# List of tabs
TABS = [
    ("Dashboard", "1"),
    ("Agent Connect Hub", "2"),
    ("Service Controls", "3"),
    ("Models Directory", "4"),
    ("Live Logs", "5"),
    ("Help & About", "6")
]

# Supported Agent Tools for quick connection
AGENT_TOOLS = [
    "OpenCode",
    "Hermes",
    "Claude Code",
    "Goose",
    "Droid",
    "Aider",
    "Cline / Roo Code",
    "Continue.dev",
    "Python / LangChain"
]


class TUIApp:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.current_tab = 0
        self.running = True

        # Selection indexes for lists inside tabs
        self.agent_selected_idx = 0
        self.action_selected_idx = 0
        self.model_selected_idx = 0

        # State cache
        self.last_status_check = 0
        self.is_healthy = False
        self.health_msg = "Checking..."
        self.latency_ms = 0.0
        self.pid = None
        self.accounts = []
        self.models = []
        self.config = {}

        # Notification / flash banner
        self.flash_message = ""
        self.flash_time = 0
        self.flash_color = 1  # green

        # Action in progress
        self.in_action = False
        self.action_name = ""
        self.test_result: Optional[Dict[str, Any]] = None

        # Logs view state
        self.log_scroll_offset = 0
        self.auto_scroll_logs = True

        # Initialize curses settings
        self.setup_curses()
        self.refresh_state(force=True)

    def color(self, pair_num: int) -> int:
        try:
            return self.color(pair_num)
        except Exception:
            return 0

    def setup_curses(self):
        try:
            curses.curs_set(0)  # Hide cursor
        except Exception:
            pass
        try:
            self.stdscr.nodelay(True)  # Non-blocking input
        except Exception:
            pass
        try:
            curses.use_default_colors()
        except Exception:
            pass

        # Initialize color pairs
        try:
            if curses.has_colors():
                curses.init_pair(1, curses.COLOR_GREEN, -1)   # Success / Running
                curses.init_pair(2, curses.COLOR_RED, -1)     # Danger / Stopped
                curses.init_pair(3, curses.COLOR_CYAN, -1)    # Primary / Active
                curses.init_pair(4, curses.COLOR_YELLOW, -1)  # Warning / Key
                curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_CYAN)  # Selected tab / button
                curses.init_pair(6, curses.COLOR_MAGENTA, -1) # Accents
                curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLUE)  # Highlighted row
                curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_WHITE) # Alert / modal
        except Exception:
            pass

    def set_flash(self, message: str, is_error: bool = False):
        self.flash_message = message
        self.flash_time = time.time()
        self.flash_color = 2 if is_error else 1

    def refresh_state(self, force: bool = False):
        now = time.time()
        # Refresh every 3 seconds or when forced
        if force or (now - self.last_status_check > 3.0):
            self.last_status_check = now
            self.pid = pm.get_proxy_pid()
            self.is_healthy, self.health_msg, self.latency_ms = pm.check_proxy_health()
            self.accounts = pm.get_auth_accounts()
            self.config = pm.load_config()
            if self.is_healthy and not self.models:
                # Fetch models in background to avoid blocking render
                threading.Thread(target=self._bg_fetch_models, daemon=True).start()

    def _bg_fetch_models(self):
        try:
            mods = pm.get_available_models()
            if mods:
                self.models = mods
        except Exception:
            pass

    def safe_addstr(self, y: int, x: int, text: str, attr=0):
        """Safely write string to window without crashing on bounds."""
        max_y, max_x = self.stdscr.getmaxyx()
        if y < 0 or y >= max_y or x < 0 or x >= max_x:
            return
        avail = max_x - x
        if avail <= 0:
            return
        try:
            self.stdscr.addstr(y, x, text[:avail], attr)
        except curses.error:
            pass

    def run(self):
        while self.running:
            self.refresh_state()
            self.render()

            try:
                ch = self.stdscr.getch()
            except Exception:
                ch = -1

            if ch != -1:
                self.handle_input(ch)

            time.sleep(0.04)

    def handle_input(self, ch: int):
        # Global shortcuts
        if ch in [ord('q'), ord('Q')]:
            self.running = False
            return
        elif ch == curses.KEY_RESIZE:
            self.stdscr.clear()
            return
        elif ch in [ord('1'), ord('2'), ord('3'), ord('4'), ord('5'), ord('6')]:
            self.current_tab = ch - ord('1')
            return
        elif ch in [ord('\t'), 9]:  # Tab key cycles tabs
            self.current_tab = (self.current_tab + 1) % len(TABS)
            return
        elif ch in [curses.KEY_BTAB]:  # Shift+Tab
            self.current_tab = (self.current_tab - 1) % len(TABS)
            return

        # Fast global action keys
        if ch in [ord('s'), ord('S')]:
            self.action_start_proxy()
            return
        elif ch in [ord('k'), ord('K')]:
            self.action_stop_proxy()
            return
        elif ch in [ord('r'), ord('R')]:
            self.action_restart_proxy()
            return
        elif ch in [ord('t'), ord('T')]:
            self.action_test_gemini()
            return

        # Tab specific controls
        if self.current_tab == 1:  # Agent Connect Hub
            self.handle_agent_tab_input(ch)
        elif self.current_tab == 2:  # Service Controls
            self.handle_controls_tab_input(ch)
        elif self.current_tab == 3:  # Models Directory
            self.handle_models_tab_input(ch)
        elif self.current_tab == 4:  # Live Logs
            self.handle_logs_tab_input(ch)

    def handle_agent_tab_input(self, ch: int):
        if ch in [curses.KEY_UP, ord('k')]:
            self.agent_selected_idx = max(0, self.agent_selected_idx - 1)
        elif ch in [curses.KEY_DOWN, ord('j')]:
            self.agent_selected_idx = min(len(AGENT_TOOLS) - 1, self.agent_selected_idx + 1)
        elif ch in [ord('e'), ord('E')]:
            # Export .env file for selected tool
            tool = AGENT_TOOLS[self.agent_selected_idx]
            path = pm.export_agent_env(tool)
            self.set_flash(f"Exported {Path(path).name} for {tool}!", is_error=False)
        elif ch in [ord('g'), ord('G')]:
            # Generate executable launcher script
            tool = AGENT_TOOLS[self.agent_selected_idx]
            path = pm.create_agent_launcher(tool)
            self.set_flash(f"Generated executable script: {Path(path).name}!", is_error=False)
        elif ch in [ord('c'), ord('C')]:
            tool = AGENT_TOOLS[self.agent_selected_idx]
            if tool == "OpenCode":
                ok, msg = pm.configure_opencode(set_default=True)
                self.set_flash("Registered 'antigravity' in ~/.config/opencode/opencode.json!", is_error=not ok)
            else:
                self.set_flash(f"No custom JSON setup needed for {tool}.", is_error=False)
        elif ch in [ord('l'), ord('L'), 10, 13]:  # Enter or L to launch launcher
            tool = AGENT_TOOLS[self.agent_selected_idx]
            self.action_launch_agent(tool)

    def handle_controls_tab_input(self, ch: int):
        ACTIONS = ["Start Proxy Server", "Stop Proxy Server", "Restart Proxy Server", "Test Gemini (Anthropic format)", "Test Gemini (OpenAI format)", "Authenticate Antigravity OAuth"]
        if ch in [curses.KEY_UP, ord('k')]:
            self.action_selected_idx = max(0, self.action_selected_idx - 1)
        elif ch in [curses.KEY_DOWN, ord('j')]:
            self.action_selected_idx = min(len(ACTIONS) - 1, self.action_selected_idx + 1)
        elif ch in [10, 13, ord(' ')]:  # Enter or Space
            idx = self.action_selected_idx
            if idx == 0:
                self.action_start_proxy()
            elif idx == 1:
                self.action_stop_proxy()
            elif idx == 2:
                self.action_restart_proxy()
            elif idx == 3:
                self.action_test_gemini(openai=False)
            elif idx == 4:
                self.action_test_gemini(openai=True)
            elif idx == 5:
                self.action_oauth_login()

    def handle_models_tab_input(self, ch: int):
        if not self.models:
            return
        if ch in [curses.KEY_UP, ord('k')]:
            self.model_selected_idx = max(0, self.model_selected_idx - 1)
        elif ch in [curses.KEY_DOWN, ord('j')]:
            self.model_selected_idx = min(len(self.models) - 1, self.model_selected_idx + 1)
        elif ch in [10, 13, ord('t'), ord('T')]:
            # Test the currently selected model
            model = self.models[self.model_selected_idx]
            self.action_test_specific_model(model)
        elif ch in [ord('d'), ord('D')]:
            # Set as default model in config.yaml
            model = self.models[self.model_selected_idx]
            ok, msg = pm.update_default_target_model(model)
            if ok:
                self.set_flash(f"Set '{model}' as default in config.yaml! Restarting...", is_error=False)
                self.action_restart_proxy()
            else:
                self.set_flash(f"Error: {msg}", is_error=True)

    def handle_logs_tab_input(self, ch: int):
        if ch in [curses.KEY_UP, ord('k')]:
            self.log_scroll_offset += 2
            self.auto_scroll_logs = False
        elif ch in [curses.KEY_DOWN, ord('j')]:
            self.log_scroll_offset = max(0, self.log_scroll_offset - 2)
            if self.log_scroll_offset == 0:
                self.auto_scroll_logs = True
        elif ch in [ord('c'), ord('C')]:
            # Reset scroll to bottom
            self.log_scroll_offset = 0
            self.auto_scroll_logs = True

    # --------------------------------------------------------------------------
    # Async / Background Action Triggers
    # --------------------------------------------------------------------------
    def action_start_proxy(self):
        self.set_flash("Starting proxy daemon...", is_error=False)
        threading.Thread(target=self._bg_start, daemon=True).start()

    def _bg_start(self):
        ok, msg = pm.start_proxy()
        self.refresh_state(force=True)
        if ok:
            self.set_flash("Proxy started and verified healthy!", is_error=False)
        else:
            self.set_flash(f"Failed to start: {msg}", is_error=True)

    def action_stop_proxy(self):
        self.set_flash("Stopping proxy daemon...", is_error=False)
        threading.Thread(target=self._bg_stop, daemon=True).start()

    def _bg_stop(self):
        ok, msg = pm.stop_proxy()
        self.refresh_state(force=True)
        self.set_flash("Proxy daemon stopped.", is_error=False)

    def action_restart_proxy(self):
        self.set_flash("Restarting proxy daemon...", is_error=False)
        threading.Thread(target=self._bg_restart, daemon=True).start()

    def _bg_restart(self):
        ok, msg = pm.restart_proxy()
        self.refresh_state(force=True)
        if ok:
            self.set_flash("Proxy restarted successfully!", is_error=False)
        else:
            self.set_flash(f"Restart error: {msg}", is_error=True)

    def action_test_gemini(self, openai: bool = False):
        mode_str = "OpenAI" if openai else "Anthropic"
        self.set_flash(f"Testing Gemini via {mode_str} API...", is_error=False)
        threading.Thread(target=self._bg_test, args=(openai,), daemon=True).start()

    def _bg_test(self, openai: bool):
        if openai:
            res = pm.test_gemini_openai(model="gemini-3.8-flash-high")
        else:
            res = pm.test_gemini_anthropic(model="claude-3-7-sonnet-20250219")
        self.test_result = res
        if res.get("success"):
            txt = res.get("text", "")
            lat = res.get("latency_ms", 0)
            self.set_flash(f"Success ({lat}ms): \"{txt}\"", is_error=False)
        else:
            err = res.get("error", "Unknown error")
            self.set_flash(f"Test failed: {err[:50]}", is_error=True)

    def action_test_specific_model(self, model: str):
        self.set_flash(f"Testing model '{model}'...", is_error=False)
        def _test():
            res = pm.test_gemini_openai(model=model, prompt="Reply in 3 words: Model test OK.")
            self.test_result = res
            if res.get("success"):
                self.set_flash(f"'{model}' OK ({res.get('latency_ms')}ms): {res.get('text')}", is_error=False)
            else:
                self.set_flash(f"'{model}' failed: {res.get('error')[:50]}", is_error=True)
        threading.Thread(target=_test, daemon=True).start()

    def action_oauth_login(self):
        """Temporarily suspend curses and invoke login-antigravity.sh."""
        curses.endwin()
        print("\n" + "=" * 64)
        print(" Antigravity OAuth Login")
        print("=" * 64)
        script = pm.BASE_DIR / "login-antigravity.sh"
        try:
            subprocess.run([str(script)], cwd=str(pm.BASE_DIR))
        except Exception as e:
            print(f"Error executing login script: {e}")
        print("\nPress Enter to return to TUI...")
        input()
        self.setup_curses()
        self.refresh_state(force=True)

    def action_launch_agent(self, tool: str):
        """Ensure launcher exists and launch in clean terminal mode."""
        launcher = pm.create_agent_launcher(tool)
        curses.endwin()
        os.system("stty sane 2>/dev/null || true")
        print("\n" + "=" * 64)
        print(f" ✦ AntiRoute: Launching {tool} ✦")
        print("=" * 64)
        print(f"Launcher: {launcher}")
        print("\nStarting now (Ctrl+C or exit agent to return)...")
        print("-" * 64)
        try:
            subprocess.run([launcher])
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"\nExecution error: {e}")
        print("-" * 64)
        print("Press Enter to return to AntiRoute TUI...")
        try:
            input()
        except (KeyboardInterrupt, EOFError):
            pass
        os.system("stty sane 2>/dev/null || true")
        self.setup_curses()
        self.stdscr.clear()
        self.refresh_state(force=True)

    # --------------------------------------------------------------------------
    # Main Render Pipeline
    # --------------------------------------------------------------------------
    def render(self):
        max_y, max_x = self.stdscr.getmaxyx()
        if max_y < 16 or max_x < 60:
            self.stdscr.clear()
            self.safe_addstr(0, 0, "Terminal window too small! Please resize to at least 80x20.", curses.A_BOLD)
            self.stdscr.refresh()
            return

        self.stdscr.erase()

        # 1. Header & Status Bar
        self.render_header(max_y, max_x)

        # 2. Tabs Bar
        self.render_tabs(max_y, max_x)

        # 3. Content Area
        content_top = 4
        content_bottom = max_y - 3
        if self.current_tab == 0:
            self.render_dashboard(content_top, content_bottom, max_x)
        elif self.current_tab == 1:
            self.render_agent_hub(content_top, content_bottom, max_x)
        elif self.current_tab == 2:
            self.render_controls(content_top, content_bottom, max_x)
        elif self.current_tab == 3:
            self.render_models(content_top, content_bottom, max_x)
        elif self.current_tab == 4:
            self.render_logs(content_top, content_bottom, max_x)
        elif self.current_tab == 5:
            self.render_help(content_top, content_bottom, max_x)

        # 4. Flash Message Bar (if active)
        if self.flash_message and (time.time() - self.flash_time < 6.0):
            flash_attr = self.color(self.flash_color) | curses.A_BOLD
            msg = f"  ▶ {self.flash_message}  "
            self.safe_addstr(max_y - 2, 2, msg, flash_attr)

        # 5. Footer & Keybindings
        self.render_footer(max_y, max_x)

        self.stdscr.refresh()

    def render_header(self, max_y: int, max_x: int):
        title = " ✦ ANTIROUTE ✦  The Antigravity AI Agent Router "
        self.safe_addstr(0, 2, title, self.color(3) | curses.A_BOLD)

        # Status Badge
        if self.is_healthy:
            status_text = f" ● PROXY: RUNNING (PID {self.pid or 'active'} | {self.latency_ms:.0f}ms) "
            badge_attr = self.color(1) | curses.A_BOLD
        else:
            status_text = " ○ PROXY: STOPPED "
            badge_attr = self.color(2) | curses.A_BOLD

        x_status = max(len(title) + 6, max_x - len(status_text) - 2)
        self.safe_addstr(0, x_status, status_text, badge_attr)

        # Sub-header: Account & URL
        account_str = self.accounts[0]["email"] if self.accounts else "No OAuth Account"
        sub = f"Account: {account_str}  │  URL: http://{self.config.get('host', '127.0.0.1')}:{self.config.get('port', 8317)}"
        self.safe_addstr(1, 2, sub, curses.A_DIM)

    def render_tabs(self, max_y: int, max_x: int):
        x = 2
        for idx, (tab_name, num) in enumerate(TABS):
            label = f" [{num}] {tab_name} "
            if idx == self.current_tab:
                attr = self.color(5) | curses.A_BOLD
            else:
                attr = curses.A_NORMAL
            self.safe_addstr(2, x, label, attr)
            x += len(label) + 2

        # Divider line
        divider = "─" * (max_x - 4)
        self.safe_addstr(3, 2, divider, curses.A_DIM)

    def render_footer(self, max_y: int, max_x: int):
        self.safe_addstr(max_y - 1, 2, "─" * (max_x - 4), curses.A_DIM)
        keys = "[Tab/1-6] Tabs  [S]tart  [K]ill  [R]estart  [T]est  [Q]uit"
        self.safe_addstr(max_y - 1, 4, keys, self.color(4))

    # --------------------------------------------------------------------------
    # Tab 0: Dashboard
    # --------------------------------------------------------------------------
    def render_dashboard(self, top: int, bottom: int, max_x: int):
        y = top + 1

        self.safe_addstr(y, 4, "SYSTEM & PROXY STATUS", self.color(3) | curses.A_BOLD)
        y += 2

        # Status box
        host = self.config.get("host", "127.0.0.1")
        port = self.config.get("port", 8317)
        status_color = self.color(1) if self.is_healthy else self.color(2)
        state_str = "HEALTHY & ACCEPTING REQUESTS" if self.is_healthy else "STOPPED / OFFLINE"

        self.safe_addstr(y, 4, f"• Service Status:    ", curses.A_BOLD)
        self.safe_addstr(y, 25, state_str, status_color | curses.A_BOLD)
        y += 1

        self.safe_addstr(y, 4, f"• Process PID:       {self.pid if self.pid else 'Not running'}")
        y += 1
        self.safe_addstr(y, 4, f"• Anthropic Base:    http://{host}:{port}  (speaks /v1/messages)")
        y += 1
        self.safe_addstr(y, 4, f"• OpenAI Base:       http://{host}:{port}/v1  (speaks /v1/chat/completions)")
        y += 1
        self.safe_addstr(y, 4, f"• Proxy API Key:     {pm.DEFAULT_API_KEY}")
        y += 2

        self.safe_addstr(y, 4, "GOOGLE ANTIGRAVITY OAUTH SESSIONS", self.color(3) | curses.A_BOLD)
        y += 2
        if self.accounts:
            for acc in self.accounts:
                self.safe_addstr(y, 4, f"✔ Account: {acc['email']}", self.color(1))
                self.safe_addstr(y + 1, 6, f"File: {acc['file']}  ({acc['size']} bytes)", curses.A_DIM)
                y += 2
        else:
            self.safe_addstr(y, 4, "⚠ No active OAuth token found! Press [3] -> Authenticate or run ./login-antigravity.sh", self.color(4))
            y += 2

        self.safe_addstr(y, 4, "QUICK ACTIONS", self.color(3) | curses.A_BOLD)
        y += 2
        self.safe_addstr(y, 4, "• Press [2] to connect OpenCode, Hermes, Claude Code, Aider, or Cline.")
        y += 1
        self.safe_addstr(y, 4, "• Press [S] to Start proxy  │  [K] to Kill/Stop  │  [R] to Restart  │  [T] to Test Gemini.")
        y += 2

        if self.test_result:
            self.safe_addstr(y, 4, "LAST TEST QUERY RESULT", self.color(3) | curses.A_BOLD)
            y += 2
            if self.test_result.get("success"):
                txt = self.test_result.get("text", "")
                lat = self.test_result.get("latency_ms", 0)
                mod = self.test_result.get("model", "")
                self.safe_addstr(y, 4, f"Model: {mod}  │  Latency: {lat}ms", curses.A_BOLD)
                y += 1
                self.safe_addstr(y, 4, f"Response: \"{txt}\"", self.color(1))
            else:
                self.safe_addstr(y, 4, f"Error: {self.test_result.get('error')}", self.color(2))

    # --------------------------------------------------------------------------
    # Tab 1: Agent Connect Hub (OpenCode, Hermes, Claude Code, etc.)
    # --------------------------------------------------------------------------
    def render_agent_hub(self, top: int, bottom: int, max_x: int):
        # Two-column layout: Left column = Agent list; Right column = Connection Details
        left_w = 26
        divider_x = left_w + 3

        # Left Column: Agent Selector
        self.safe_addstr(top + 1, 4, "SELECT AGENT TOOL", self.color(3) | curses.A_BOLD)
        y = top + 3
        for idx, tool in enumerate(AGENT_TOOLS):
            is_sel = (idx == self.agent_selected_idx)
            attr = self.color(7) | curses.A_BOLD if is_sel else curses.A_NORMAL
            prefix = "▶ " if is_sel else "  "
            self.safe_addstr(y, 4, f"{prefix}{tool.ljust(left_w - 4)}", attr)
            y += 1

        # Vertical Divider
        for line_y in range(top + 1, bottom):
            self.safe_addstr(line_y, divider_x, "│", curses.A_DIM)

        # Right Column: Tool Connection Details
        right_x = divider_x + 3
        selected_tool = AGENT_TOOLS[self.agent_selected_idx]
        info = pm.get_agent_connection_info(selected_tool)

        ry = top + 1
        self.safe_addstr(ry, right_x, f"INTEGRATION: {info['name'].upper()}", self.color(3) | curses.A_BOLD)
        ry += 1
        self.safe_addstr(ry, right_x, info["description"], curses.A_DIM)
        ry += 2

        # Action Buttons for this tool
        if selected_tool == "OpenCode":
            btn_str = "[E] Export .env  │  [C] Auto-Configure  │  [L/Enter] Launch Now"
        else:
            btn_str = "[E] Export .env  │  [G] Generate Launcher  │  [L/Enter] Launch Now"
        self.safe_addstr(ry, right_x, btn_str, self.color(4) | curses.A_BOLD)
        ry += 2

        # Environment Variables
        if info["env"]:
            self.safe_addstr(ry, right_x, "Environment Variables:", curses.A_BOLD)
            ry += 1
            for k, v in info["env"].items():
                self.safe_addstr(ry, right_x + 2, f"export {k}=\"{v}\"", self.color(1))
                ry += 1
            ry += 1

        # Configuration snippet / How to use
        self.safe_addstr(ry, right_x, "Configuration / Command Instructions:", curses.A_BOLD)
        ry += 1
        snippet_lines = info["snippet"].splitlines()
        for sline in snippet_lines:
            if ry >= bottom:
                break
            if sline.startswith("#") or sline.startswith("//"):
                attr = curses.A_DIM
            elif "export" in sline or "run" in sline or "aider" in sline or "opencode" in sline or "hermes" in sline:
                attr = self.color(1)
            else:
                attr = curses.A_NORMAL
            self.safe_addstr(ry, right_x + 2, sline, attr)
            ry += 1

    # --------------------------------------------------------------------------
    # Tab 2: Service Controls
    # --------------------------------------------------------------------------
    def render_controls(self, top: int, bottom: int, max_x: int):
        ACTIONS = [
            ("Start Proxy Server", "Launches cli-proxy-api daemon in background on port 8317"),
            ("Stop Proxy Server", "Gracefully kills the running cli-proxy-api daemon"),
            ("Restart Proxy Server", "Shuts down and restarts the proxy server"),
            ("Test Gemini (Anthropic /v1/messages)", "Sends test prompt to Anthropic translation endpoint"),
            ("Test Gemini (OpenAI /v1/chat/completions)", "Sends test prompt to OpenAI translation endpoint"),
            ("Authenticate Antigravity OAuth", "Opens browser/token auth for Google Antigravity account")
        ]

        self.safe_addstr(top + 1, 4, "PROXY SERVICE ACTIONS & OPERATIONS", self.color(3) | curses.A_BOLD)
        self.safe_addstr(top + 2, 4, "Use [↑/↓] or [j/k] to navigate, [Enter] or [Space] to execute action.", curses.A_DIM)

        y = top + 4
        for idx, (act, desc) in enumerate(ACTIONS):
            is_sel = (idx == self.action_selected_idx)
            attr = self.color(7) | curses.A_BOLD if is_sel else curses.A_BOLD
            prefix = " ▶ [ENTER] " if is_sel else "   [     ] "
            self.safe_addstr(y, 4, f"{prefix}{act}", attr)
            self.safe_addstr(y + 1, 15, f"{desc}", curses.A_DIM)
            y += 3

        if self.test_result:
            y = max(y, bottom - 5)
            self.safe_addstr(y, 4, "─────────────────────────────────────────────────────────────", curses.A_DIM)
            y += 1
            if self.test_result.get("success"):
                self.safe_addstr(y, 4, f"✔ Test Passed ({self.test_result.get('latency_ms')}ms): {self.test_result.get('text')}", self.color(1) | curses.A_BOLD)
            else:
                self.safe_addstr(y, 4, f"✖ Test Failed: {self.test_result.get('error')}", self.color(2) | curses.A_BOLD)

    # --------------------------------------------------------------------------
    # Tab 3: Models Directory
    # --------------------------------------------------------------------------
    def render_models(self, top: int, bottom: int, max_x: int):
        self.safe_addstr(top + 1, 4, "AVAILABLE PROXY MODELS (from /v1/models)", self.color(3) | curses.A_BOLD)
        self.safe_addstr(top + 2, 4, "Press [T/Enter] to test model  │  Press [D] to set as default backend in config.yaml", curses.A_DIM)

        if not self.models:
            self.safe_addstr(top + 4, 4, "Loading models from proxy (make sure proxy is running)...", self.color(4))
            return

        visible_height = bottom - top - 5
        start_idx = max(0, self.model_selected_idx - visible_height + 1)
        end_idx = min(len(self.models), start_idx + visible_height)

        y = top + 4
        for idx in range(start_idx, end_idx):
            model = self.models[idx]
            is_sel = (idx == self.model_selected_idx)
            attr = self.color(7) | curses.A_BOLD if is_sel else curses.A_NORMAL
            prefix = " ▶ " if is_sel else "   "
            self.safe_addstr(y, 4, f"{prefix}{model.ljust(45)}", attr)
            y += 1

    # --------------------------------------------------------------------------
    # Tab 4: Live Logs
    # --------------------------------------------------------------------------
    def render_logs(self, top: int, bottom: int, max_x: int):
        self.safe_addstr(top + 1, 4, "PROXY LOG VIEWER (proxy.log)", self.color(3) | curses.A_BOLD)
        scroll_status = "Auto-scrolling (Press [↑] to scroll up, [C] to snap to bottom)" if self.auto_scroll_logs else f"Scrolled up {self.log_scroll_offset} lines (Press [C] to resume auto-scroll)"
        self.safe_addstr(top + 2, 4, scroll_status, curses.A_DIM)

        visible_height = bottom - top - 4
        all_logs = pm.get_recent_logs(lines=120)

        if self.auto_scroll_logs:
            displayed = all_logs[-visible_height:] if len(all_logs) > visible_height else all_logs
        else:
            total = len(all_logs)
            end = max(visible_height, total - self.log_scroll_offset)
            start = max(0, end - visible_height)
            displayed = all_logs[start:end]

        y = top + 4
        for line in displayed:
            if y >= bottom:
                break
            # Color code log lines
            if "error" in line.lower() or "fail" in line.lower():
                attr = self.color(2)
            elif "success" in line.lower() or "ok" in line.lower() or "200" in line:
                attr = self.color(1)
            elif "warn" in line.lower():
                attr = self.color(4)
            else:
                attr = curses.A_NORMAL
            self.safe_addstr(y, 4, line, attr)
            y += 1

    # --------------------------------------------------------------------------
    # Tab 5: Help & About
    # --------------------------------------------------------------------------
    def render_help(self, top: int, bottom: int, max_x: int):
        y = top + 1
        self.safe_addstr(y, 4, "ABOUT ANTIROUTE", self.color(3) | curses.A_BOLD)
        y += 2
        self.safe_addstr(y, 4, "AntiRoute bridges Google Antigravity's Gemini models with AI coding agents.")
        y += 1
        self.safe_addstr(y, 4, "Supported protocols: Anthropic Messages API (/v1/messages) & OpenAI API (/v1/chat/completions).")
        y += 2

        self.safe_addstr(y, 4, "QUICK NAVIGATION KEYS", self.color(3) | curses.A_BOLD)
        y += 2
        self.safe_addstr(y, 4, "• [1] - [6] or [Tab] : Switch tabs")
        y += 1
        self.safe_addstr(y, 4, "• [↑] / [↓] or [k] / [j] : Navigate lists and selectors")
        y += 1
        self.safe_addstr(y, 4, "• [S] : Start proxy daemon")
        y += 1
        self.safe_addstr(y, 4, "• [K] : Kill / Stop proxy daemon")
        y += 1
        self.safe_addstr(y, 4, "• [R] : Restart proxy daemon")
        y += 1
        self.safe_addstr(y, 4, "• [T] : Run test query against Gemini")
        y += 1
        self.safe_addstr(y, 4, "• [Q] : Exit TUI application")
        y += 2

        self.safe_addstr(y, 4, "HOW TO CONNECT AGENTS VIA CLI WITHOUT TUI", self.color(3) | curses.A_BOLD)
        y += 2
        self.safe_addstr(y, 4, "• OpenCode:      export OPENAI_BASE_URL=\"http://127.0.0.1:8317/v1\" && opencode")
        y += 1
        self.safe_addstr(y, 4, "• Hermes:        export OPENAI_BASE_URL=\"http://127.0.0.1:8317/v1\" && hermes")
        y += 1
        self.safe_addstr(y, 4, "• Claude Code:   export ANTHROPIC_BASE_URL=\"http://127.0.0.1:8317\" && claude")
        y += 1
        self.safe_addstr(y, 4, "• Aider:         aider --openai-api-base http://127.0.0.1:8317/v1")


# ------------------------------------------------------------------------------
# CLI / Non-interactive Command Line Fallbacks
# ------------------------------------------------------------------------------
def run_cli_commands():
    parser = argparse.ArgumentParser(
        prog="antiroute",
        description="AntiRoute — Antigravity AI Agent Router & TUI (Claude Code, Hermes, OpenCode)"
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("tui", help="Launch interactive AntiRoute TUI cockpit")
    subparsers.add_parser("status", help="Print health and proxy status")
    subparsers.add_parser("start", help="Start background proxy server")
    subparsers.add_parser("stop", help="Stop proxy server")
    subparsers.add_parser("restart", help="Restart proxy server")
    subparsers.add_parser("test", help="Test Gemini connection via proxy")

    conn_parser = subparsers.add_parser("connect", help="Get connection parameters for an agent tool")
    conn_parser.add_argument("tool", nargs="?", choices=["opencode", "hermes", "claude", "aider", "cline", "continue", "goose", "droid"], default=None, help="Tool name")
    conn_parser.add_argument("--export", action="store_true", help="Export to a .env file")

    args = parser.parse_args()

    if not args.command or args.command == "tui":
        # Launch TUI
        curses.wrapper(lambda stdscr: TUIApp(stdscr).run())
        return

    if args.command == "status":
        pid = pm.get_proxy_pid()
        healthy, msg, lat = pm.check_proxy_health()
        accounts = pm.get_auth_accounts()
        print("==================================================================")
        print(" ✦ AntiRoute Status & Health ✦")
        print("==================================================================")
        print(f"Service Status: {'RUNNING' if healthy else 'STOPPED'}")
        if pid:
            print(f"Process PID:    {pid}")
        print(f"Health Check:   {'OK' if healthy else 'FAIL'} ({lat:.1f}ms) - {msg}")
        print("OAuth Accounts:")
        for a in accounts:
            print(f"  - {a['email']} ({a['file']})")
        print("==================================================================")

    elif args.command == "start":
        print("Starting proxy...")
        ok, msg = pm.start_proxy()
        print(msg)

    elif args.command == "stop":
        print("Stopping proxy...")
        ok, msg = pm.stop_proxy()
        print(msg)

    elif args.command == "restart":
        print("Restarting proxy...")
        ok, msg = pm.restart_proxy()
        print(msg)

    elif args.command == "test":
        print("Testing Anthropic endpoint (/v1/messages)...")
        res1 = pm.test_gemini_anthropic()
        print(f"Result: {res1.get('text')} ({res1.get('latency_ms')}ms)")
        print("\nTesting OpenAI endpoint (/v1/chat/completions)...")
        res2 = pm.test_gemini_openai()
        print(f"Result: {res2.get('text')} ({res2.get('latency_ms')}ms)")

    elif args.command == "connect":
        if not args.tool:
            print("==================================================================")
            print(" Supported Agent Integrations & Quick Connect Commands")
            print("==================================================================")
            tools_list = ["hermes", "opencode", "claude", "goose", "droid", "aider"]
            for t in tools_list:
                inf = pm.get_agent_connection_info(t)
                print(f"• {inf['name']}:")
                if inf["commands"]:
                    print(f"    Command: {inf['commands'][-1]}")
                print(f"    Export:  source ./export-env.sh {t}")
                print(f"    Docs:    ./tui.sh connect {t}")
                print()
            print("To view full config or export .env:")
            print("  ./tui.sh connect <tool> [--export]")
            print("==================================================================")
            return

        info = pm.get_agent_connection_info(args.tool)
        print(f"Connection parameters for {info['name']}:")
        print("-" * 50)
        for k, v in info["env"].items():
            print(f'export {k}="{v}"')
        print("-" * 50)
        print(info["snippet"])
        if args.export:
            fpath = pm.export_agent_env(args.tool)
            print(f"\n✔ Successfully exported to: {fpath}")


if __name__ == "__main__":
    try:
        run_cli_commands()
    except KeyboardInterrupt:
        print("\nExiting.")
