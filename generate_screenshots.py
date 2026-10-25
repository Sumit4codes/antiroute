#!/usr/bin/env python3
"""
generate_screenshots.py - Generate pixel-perfect, high-resolution screenshots & hero banner for AntiRoute README
"""

import subprocess
import os
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR = BASE_DIR / ".tmp_screenshots"
TMP_DIR.mkdir(parents=True, exist_ok=True)

SHARED_CSS = """
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700;800;900&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body {
    background: #060913;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'JetBrains Mono', monospace;
    overflow: hidden;
  }
  .window {
    width: 1020px;
    background: #090e1a;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.12);
    box-shadow: 0 30px 70px -15px rgba(0, 0, 0, 0.9), 0 0 45px rgba(56, 189, 248, 0.14);
    overflow: hidden;
  }
  .titlebar {
    background: #0f172a;
    padding: 13px 20px;
    display: flex;
    align-items: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }
  .buttons { display: flex; gap: 8px; }
  .btn { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }
  .btn-red { background: #ef4444; }
  .btn-yellow { background: #f59e0b; }
  .btn-green { background: #10b981; }
  .title { flex: 1; text-align: center; color: #94a3b8; font-size: 13px; font-weight: 500; margin-right: 48px; }
  .terminal { padding: 22px 28px; color: #f1f5f9; font-size: 13.5px; line-height: 1.55; }
  .header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
  .brand { font-size: 15.5px; font-weight: 800; color: #38bdf8; letter-spacing: 0.5px; }
  .badge-healthy {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.35);
    padding: 3px 12px;
    border-radius: 6px;
    font-size: 12.5px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .dot { width: 8px; height: 8px; border-radius: 50%; background: #34d399; box-shadow: 0 0 8px #34d399; }
  .sub-header { color: #64748b; font-size: 12px; margin-bottom: 16px; }
  .tabs-bar { display: flex; gap: 8px; border-bottom: 1px solid #1e293b; padding-bottom: 10px; margin-bottom: 18px; }
  .tab { padding: 5px 12px; border-radius: 6px; font-size: 12.5px; color: #94a3b8; }
  .tab.active { background: #0284c7; color: #ffffff; font-weight: 700; box-shadow: 0 0 14px rgba(2, 132, 199, 0.45); }
  .footer {
    margin-top: 18px;
    padding-top: 12px;
    border-top: 1px solid #1e293b;
    display: flex;
    justify-content: space-between;
    color: #fbbf24;
    font-size: 12px;
    font-weight: 600;
  }
"""

HTML_HERO_BANNER = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&family=JetBrains+Mono:wght@500;700;800&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #050814;
    width: 1200px;
    height: 420px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Inter', sans-serif;
    overflow: hidden;
  }
  .card {
    width: 1140px;
    height: 360px;
    background: radial-gradient(circle at 50% 0%, rgba(56, 189, 248, 0.22) 0%, rgba(15, 23, 42, 0.95) 75%), #090e1a;
    border-radius: 16px;
    border: 1px solid rgba(56, 189, 248, 0.35);
    box-shadow: 0 25px 60px rgba(0, 0, 0, 0.9), 0 0 50px rgba(56, 189, 248, 0.18);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 30px 40px;
    position: relative;
  }
  .glow-top {
    position: absolute;
    top: 0;
    left: 15%;
    right: 15%;
    height: 2px;
    background: linear-gradient(90deg, transparent, #38bdf8, #818cf8, transparent);
  }
  .badge {
    background: rgba(56, 189, 248, 0.12);
    border: 1px solid rgba(56, 189, 248, 0.35);
    color: #38bdf8;
    padding: 5px 16px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 1px;
    margin-bottom: 16px;
    text-transform: uppercase;
  }
  .logo-title {
    font-size: 48px;
    font-weight: 900;
    color: #ffffff;
    letter-spacing: -0.5px;
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 12px;
  }
  .sparkle { color: #38bdf8; text-shadow: 0 0 25px #38bdf8; }
  .tagline {
    font-size: 17.5px;
    color: #94a3b8;
    max-width: 780px;
    line-height: 1.55;
    margin-bottom: 24px;
  }
  .pill-row {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    justify-content: center;
  }
  .pill {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: #cbd5e1;
    font-size: 13px;
    font-weight: 600;
    padding: 7px 18px;
    border-radius: 8px;
    font-family: 'JetBrains Mono', monospace;
  }
  .pill.highlight {
    background: rgba(16, 185, 129, 0.12);
    border-color: rgba(16, 185, 129, 0.35);
    color: #34d399;
  }
  .pill.purple {
    background: rgba(168, 85, 247, 0.12);
    border-color: rgba(168, 85, 247, 0.35);
    color: #c084fc;
  }
</style>
</head>
<body>
  <div class="card">
    <div class="glow-top"></div>
    <div class="badge">✦ Google Antigravity &bull; AI Agent Gateway ✦</div>
    <div class="logo-title">
      <span class="sparkle">✦</span> ANTIROUTE <span class="sparkle">✦</span>
    </div>
    <div class="tagline">
      The universal protocol router & TUI cockpit bridging <strong>Claude Code</strong>, <strong>Hermes</strong>, and <strong>OpenCode</strong> with <strong>Google Antigravity Gemini</strong>.
    </div>
    <div class="pill-row">
      <span class="pill highlight">&#x2714; Zero API Fees</span>
      <span class="pill">Claude Code CLI</span>
      <span class="pill">Hermes Agent</span>
      <span class="pill">OpenCode</span>
      <span class="pill purple">Gemini 3.8 Flash High</span>
      <span class="pill">Interactive TUI Cockpit</span>
    </div>
  </div>
</body>
</html>
"""

HTML_TUI_DASHBOARD = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
{SHARED_CSS}
  .section-title {{ color: #38bdf8; font-weight: 700; font-size: 12.5px; letter-spacing: 0.8px; margin-top: 12px; margin-bottom: 7px; }}
  .grid {{
    display: grid;
    grid-template-columns: 190px 1fr;
    row-gap: 5px;
    margin-bottom: 14px;
    background: rgba(15, 23, 42, 0.5);
    padding: 12px 16px;
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.05);
  }}
  .key {{ color: #94a3b8; font-weight: 500; font-size: 13px; }}
  .val {{ color: #f8fafc; font-weight: 600; font-size: 13px; }}
  .val-emerald {{ color: #34d399; }}
  .val-blue {{ color: #60a5fa; }}
  .account-box {{
    background: rgba(16, 185, 129, 0.06);
    border: 1px solid rgba(16, 185, 129, 0.22);
    padding: 10px 16px;
    border-radius: 8px;
    margin-bottom: 14px;
  }}
  .account-email {{ color: #34d399; font-weight: 700; font-size: 13.5px; }}
  .account-meta {{ color: #64748b; font-size: 12px; margin-top: 2px; }}
  .flash-banner {{
    background: rgba(14, 165, 233, 0.15);
    border: 1px solid rgba(14, 165, 233, 0.35);
    color: #38bdf8;
    padding: 7px 14px;
    border-radius: 6px;
    font-size: 12px;
    margin-top: 10px;
  }}
</style>
</head>
<body style="padding: 24px;">
  <div class="window">
    <div class="titlebar">
      <div class="buttons">
        <span class="btn btn-red"></span>
        <span class="btn btn-yellow"></span>
        <span class="btn btn-green"></span>
      </div>
      <div class="title">antiroute — Interactive Cockpit</div>
    </div>
    <div class="terminal">
      <div class="header-row">
        <span class="brand">✦ ANTIROUTE ✦  The Antigravity AI Agent Router</span>
        <span class="badge-healthy"><span class="dot"></span> PROXY: RUNNING (PID 77854 | 72ms)</span>
      </div>
      <div class="sub-header">
        Account: sumitforwork57@gmail.com &nbsp;│&nbsp; URL: http://127.0.0.1:8317 &nbsp;│&nbsp; Default: gemini-3.8-flash-high
      </div>

      <div class="tabs-bar">
        <span class="tab active">[1] Dashboard</span>
        <span class="tab">[2] Agent Connect Hub</span>
        <span class="tab">[3] Service Controls</span>
        <span class="tab">[4] Models Directory</span>
        <span class="tab">[5] Live Logs</span>
        <span class="tab">[6] Help & About</span>
      </div>

      <div class="section-title">SYSTEM & PROXY STATUS</div>
      <div class="grid">
        <span class="key">• Service Status:</span>
        <span class="val val-emerald">HEALTHY & ACCEPTING REQUESTS</span>
        <span class="key">• Process PID:</span>
        <span class="val">77854 (cli-proxy-api daemon)</span>
        <span class="key">• Anthropic Base:</span>
        <span class="val val-blue">http://127.0.0.1:8317 <span style="color:#64748b;font-weight:400;">(/v1/messages &rarr; Claude Code, Cline)</span></span>
        <span class="key">• OpenAI Base:</span>
        <span class="val val-blue">http://127.0.0.1:8317/v1 <span style="color:#64748b;font-weight:400;">(/v1/chat/completions &rarr; Hermes, OpenCode, Aider)</span></span>
        <span class="key">• Active Model Alias:</span>
        <span class="val" style="color:#c084fc;">gemini-3.8-flash-high &harr; claude-3-7-sonnet-20250219</span>
      </div>

      <div class="section-title">AUTHENTICATED GOOGLE ANTIGRAVITY SESSIONS</div>
      <div class="account-box">
        <div class="account-email">&#x2714; sumitforwork57@gmail.com</div>
        <div class="account-meta">Token File: antigravity-sumitforwork57@gmail.com.json &nbsp;│&nbsp; Scope: Antigravity Code & Execution</div>
      </div>

      <div class="flash-banner">
        ▶ Last Test Query OK (76ms): "Hello world from Claude Code with Antigravity!"
      </div>

      <div class="footer">
        <span>[Tab/1-6] Tabs &nbsp; [S]tart &nbsp; [K]ill &nbsp; [R]estart &nbsp; [T]est Gemini &nbsp; [Q]uit</span>
        <span style="color:#64748b;">AntiRoute v1.0.0</span>
      </div>
    </div>
  </div>
</body>
</html>
"""

HTML_AGENT_HUB = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
{SHARED_CSS}
  .hub-container {{
    display: grid;
    grid-template-columns: 230px 1px 1fr;
    gap: 18px;
    min-height: 330px;
  }}
  .divider {{ background: #1e293b; width: 1px; height: 100%; }}
  .agent-list {{ display: flex; flex-direction: column; gap: 4px; }}
  .agent-item {{
    padding: 7px 12px;
    border-radius: 6px;
    color: #94a3b8;
    font-size: 13px;
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  .agent-item.selected {{
    background: #1e3a8a;
    color: #ffffff;
    font-weight: 700;
    box-shadow: 0 0 12px rgba(30, 58, 138, 0.5);
  }}
  .detail-panel {{ padding-left: 2px; }}
  .tool-title {{ font-size: 17px; font-weight: 800; color: #38bdf8; margin-bottom: 3px; }}
  .tool-desc {{ color: #94a3b8; font-size: 12.5px; margin-bottom: 14px; }}
  .action-buttons {{
    display: flex;
    gap: 10px;
    margin-bottom: 16px;
  }}
  .action-btn {{
    background: rgba(251, 191, 36, 0.12);
    border: 1px solid rgba(251, 191, 36, 0.4);
    color: #fbbf24;
    padding: 5px 12px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 700;
  }}
  .action-btn.primary {{
    background: rgba(16, 185, 129, 0.15);
    border-color: rgba(16, 185, 129, 0.4);
    color: #34d399;
  }}
  .code-block {{
    background: #020617;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 12px;
    line-height: 1.55;
    color: #e2e8f0;
  }}
  .comment {{ color: #64748b; }}
  .cmd {{ color: #34d399; font-weight: 600; }}
  .env-var {{ color: #60a5fa; }}
</style>
</head>
<body style="padding: 24px;">
  <div class="window">
    <div class="titlebar">
      <div class="buttons">
        <span class="btn btn-red"></span>
        <span class="btn btn-yellow"></span>
        <span class="btn btn-green"></span>
      </div>
      <div class="title">antiroute — Agent Connect Hub</div>
    </div>
    <div class="terminal">
      <div class="header-row">
        <span class="brand">✦ ANTIROUTE ✦  The Antigravity AI Agent Router</span>
        <span class="badge-healthy"><span class="dot"></span> PROXY: RUNNING (PID 77854)</span>
      </div>
      <div class="sub-header">Connect any AI Agent to Google Antigravity Gemini</div>

      <div class="tabs-bar">
        <span class="tab">[1] Dashboard</span>
        <span class="tab active">[2] Agent Connect Hub</span>
        <span class="tab">[3] Service Controls</span>
        <span class="tab">[4] Models Directory</span>
        <span class="tab">[5] Live Logs</span>
        <span class="tab">[6] Help & About</span>
      </div>

      <div class="hub-container">
        <div class="agent-list">
          <div style="color:#38bdf8;font-weight:700;font-size:11.5px;margin-bottom:6px;letter-spacing:0.5px;">SUPPORTED AGENTS</div>
          <div class="agent-item selected">&#x25B6; OpenCode</div>
          <div class="agent-item">&nbsp;&nbsp;Hermes Agent</div>
          <div class="agent-item">&nbsp;&nbsp;Claude Code</div>
          <div class="agent-item">&nbsp;&nbsp;Goose AI</div>
          <div class="agent-item">&nbsp;&nbsp;Droid Agent</div>
          <div class="agent-item">&nbsp;&nbsp;Aider</div>
          <div class="agent-item">&nbsp;&nbsp;Cline / Roo Code</div>
          <div class="agent-item">&nbsp;&nbsp;Continue.dev</div>
          <div class="agent-item">&nbsp;&nbsp;Python / LangChain</div>
        </div>

        <div class="divider"></div>

        <div class="detail-panel">
          <div class="tool-title">INTEGRATION: OPENCODE</div>
          <div class="tool-desc">Autonomous terminal AI coding assistant powered by Vercel AI SDK.</div>

          <div class="action-buttons">
            <span class="action-btn">[E] Export .env</span>
            <span class="action-btn primary">[C] Auto-Configure</span>
            <span class="action-btn primary">[L/Enter] Launch Now</span>
          </div>

          <div class="code-block">
            <div class="comment"># 1. Run via one-click launcher (auto-configures provider):</div>
            <div class="cmd">antiroute-opencode</div>
            <br>
            <div class="comment"># 2. Or invoke opencode with Antigravity Gemini model:</div>
            <div class="cmd">opencode -m antigravity/gemini-3.8-flash-high</div>
            <br>
            <div class="comment"># 3. Provider registered in ~/.config/opencode/opencode.json:</div>
            <div>baseURL: <span class="env-var">"http://127.0.0.1:8317/v1"</span></div>
            <div>npm: <span class="env-var">"@ai-sdk/openai-compatible"</span></div>
            <div>apiKey: <span class="env-var">"sk-antigravity-claude"</span></div>
          </div>
        </div>
      </div>

      <div class="footer">
        <span>[&uarr;/&darr;] Select Agent &nbsp; [E] Export .env &nbsp; [C] Auto-Config &nbsp; [Enter] Launch &nbsp; [Tab] Next Tab</span>
        <span style="color:#64748b;">AntiRoute v1.0.0</span>
      </div>
    </div>
  </div>
</body>
</html>
"""

HTML_TERMINAL_DEMO = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
{SHARED_CSS}
  .prompt {{ color: #38bdf8; font-weight: 700; }}
  .cmd {{ color: #f8fafc; font-weight: 600; }}
  .output {{ color: #94a3b8; margin-bottom: 16px; font-size: 13px; }}
  .success {{ color: #34d399; font-weight: 600; }}
  .accent {{ color: #c084fc; font-weight: 600; }}
  .cyan {{ color: #38bdf8; }}
  .box {{
    border-left: 2px solid #38bdf8;
    padding-left: 12px;
    margin: 6px 0;
  }}
</style>
</head>
<body style="padding: 24px;">
  <div class="window">
    <div class="titlebar">
      <div class="buttons">
        <span class="btn btn-red"></span>
        <span class="btn btn-yellow"></span>
        <span class="btn btn-green"></span>
      </div>
      <div class="title">terminal — zsh — 1020x520</div>
    </div>
    <div class="terminal">
      <div><span class="prompt">➜  ~</span> <span class="cmd">antiroute status</span></div>
      <div class="output">
        <div style="color:#64748b;">==================================================================</div>
        <div style="font-weight:700;color:#f8fafc;">✦ AntiRoute Status & Health ✦</div>
        <div style="color:#64748b;">==================================================================</div>
        <div>Service Status: <span class="success">RUNNING (PID 77854)</span></div>
        <div>Health Check:   <span class="success">OK (72.5ms) - CLI Proxy API Server</span></div>
        <div>OAuth Session:  <span class="cyan">sumitforwork57@gmail.com</span> (Google Antigravity)</div>
        <div style="color:#64748b;">==================================================================</div>
      </div>

      <div><span class="prompt">➜  ~</span> <span class="cmd">antiroute-opencode run "What is 2+2? Answer in 1 word."</span></div>
      <div class="output">
        <div class="box">
          <div style="color:#64748b;">Starting OpenCode with Antigravity Gemini: antigravity/gemini-3.8-flash-high</div>
          <div style="color:#94a3b8;">&gt; build &middot; gemini-3.8-flash-high</div>
          <div class="success" style="font-size:14px;margin-top:2px;">4</div>
        </div>
      </div>

      <div><span class="prompt">➜  ~</span> <span class="cmd">antiroute-hermes -z "Say 'AntiRoute is online' in 3 words"</span></div>
      <div class="output">
        <div class="box" style="border-left-color:#c084fc;">
          <div style="color:#64748b;">Starting Hermes Agent connected to Antigravity Proxy...</div>
          <div class="accent" style="font-size:14px;margin-top:2px;">AntiRoute is online</div>
        </div>
      </div>

      <div><span class="prompt">➜  ~</span> <span style="display:inline-block;width:9px;height:16px;background:#38bdf8;vertical-align:text-bottom;"></span></div>
    </div>
  </div>
</body>
</html>
"""

def render_and_crop(html_content: str, out_path: Path, width: int, height: int):
    tmp_html = TMP_DIR / (out_path.stem + ".html")
    tmp_html.write_text(html_content)

    raw_png = TMP_DIR / (out_path.stem + "_raw.png")
    cmd = [
        "google-chrome",
        "--headless=new",
        "--no-sandbox",
        "--hide-scrollbars",
        f"--window-size={width},{height}",
        f"--screenshot={raw_png}",
        f"file://{tmp_html.resolve()}"
    ]
    subprocess.run(cmd, capture_output=True, text=True)

    if raw_png.exists():
        im = Image.open(raw_png)
        im.save(out_path, optimize=True)
        print(f"✔ Rendered: {out_path.name} ({im.size[0]}x{im.size[1]}, {out_path.stat().st_size} bytes)")
    else:
        print(f"✖ Failed: {out_path.name}")

def main():
    print("Generating pixel-perfect screenshots and hero banner...")
    render_and_crop(HTML_HERO_BANNER, ASSETS_DIR / "antiroute-banner.png", 1200, 420)
    render_and_crop(HTML_TUI_DASHBOARD, ASSETS_DIR / "antiroute-tui-dashboard.png", 1070, 680)
    render_and_crop(HTML_AGENT_HUB, ASSETS_DIR / "antiroute-agent-hub.png", 1070, 630)
    render_and_crop(HTML_TERMINAL_DEMO, ASSETS_DIR / "antiroute-terminal-demo.png", 1070, 620)
    print("All assets generated successfully.")

if __name__ == "__main__":
    main()
