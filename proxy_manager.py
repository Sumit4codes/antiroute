"""
AntiRoute - Core Backend Manager & Protocol Router
Bridges Google Antigravity's Gemini models with AI coding agents (Claude Code, Hermes, OpenCode, Aider, etc.)
"""

import os
import sys
import json
import time
import signal
import socket
import urllib.request
import urllib.error
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.yaml"
PID_PATH = BASE_DIR / "proxy.pid"
LOG_PATH = BASE_DIR / "proxy.log"
AUTH_DIR = BASE_DIR / ".auth"
BINARY_PATH = BASE_DIR / "cli-proxy-api"

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8317
DEFAULT_API_KEY = "sk-antigravity-claude"


def get_proxy_pid() -> Optional[int]:
    """Return running proxy PID if process is alive, else None."""
    if PID_PATH.exists():
        try:
            pid_str = PID_PATH.read_text().strip()
            if pid_str:
                pid = int(pid_str)
                # Check if process is alive
                os.kill(pid, 0)
                return pid
        except (ValueError, OSError):
            pass

    # Fallback: check pgrep for cli-proxy-api
    try:
        res = subprocess.run(["pgrep", "-f", "cli-proxy-api.*config"], capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            pids = [int(p) for p in res.stdout.strip().splitlines() if p.isdigit()]
            if pids:
                return pids[0]
    except Exception:
        pass

    return None


def is_port_in_use(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> bool:
    """Check if the given host:port is accepting connections."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def check_proxy_health(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> Tuple[bool, str, float]:
    """
    Check HTTP health on http://{host}:{port}/
    Returns: (is_healthy, message, latency_ms)
    """
    url = f"http://{host}:{port}/"
    start = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Antigravity-TUI"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            latency = (time.time() - start) * 1000
            data = resp.read().decode("utf-8")
            try:
                js = json.loads(data)
                msg = js.get("message", "OK")
                return True, msg, latency
            except Exception:
                return True, "OK", latency
    except Exception as e:
        latency = (time.time() - start) * 1000
        return False, str(e), latency


def get_auth_accounts() -> List[Dict[str, Any]]:
    """List authenticated Antigravity Google accounts in .auth directory."""
    accounts = []
    if not AUTH_DIR.exists():
        return accounts

    for f in AUTH_DIR.glob("*.json"):
        account = {
            "file": f.name,
            "path": str(f),
            "email": "Unknown",
            "size": f.stat().st_size,
            "mtime": f.stat().st_mtime
        }
        # Parse email from filename e.g. antigravity-email@example.com.json
        stem = f.stem
        if stem.startswith("antigravity-"):
            account["email"] = stem[len("antigravity-"):]
        else:
            account["email"] = stem

        try:
            with open(f, "r") as fp:
                data = json.load(fp)
                if isinstance(data, dict):
                    if "email" in data:
                        account["email"] = data["email"]
                    if "expires_at" in data:
                        account["expires_at"] = data["expires_at"]
        except Exception:
            pass

        accounts.append(account)
    return accounts


def load_config() -> Dict[str, Any]:
    """Parse key values from config.yaml without requiring pyyaml."""
    config = {
        "host": DEFAULT_HOST,
        "port": DEFAULT_PORT,
        "api_keys": [DEFAULT_API_KEY],
        "auth_dir": str(AUTH_DIR),
        "aliases": []
    }
    if not CONFIG_PATH.exists():
        return config

    try:
        lines = CONFIG_PATH.read_text().splitlines()
        current_alias = {}
        for line in lines:
            line_str = line.strip()
            if line_str.startswith("host:"):
                config["host"] = line_str.split(":", 1)[1].strip().strip('"\'')
            elif line_str.startswith("port:"):
                try:
                    config["port"] = int(line_str.split(":", 1)[1].strip())
                except ValueError:
                    pass
            elif line_str.startswith("- \"sk-") or line_str.startswith("- 'sk-"):
                key = line_str.lstrip("- ").strip('"\'')
                config["api_keys"] = [key]
            elif line_str.startswith("name:"):
                if current_alias.get("name") and current_alias.get("alias"):
                    config["aliases"].append(current_alias)
                current_alias = {"name": line_str.split(":", 1)[1].strip().strip('"\'')}
            elif line_str.startswith("alias:"):
                current_alias["alias"] = line_str.split(":", 1)[1].strip().strip('"\'')
        if current_alias.get("name") and current_alias.get("alias"):
            config["aliases"].append(current_alias)
    except Exception:
        pass

    return config


def start_proxy() -> Tuple[bool, str]:
    """Start the proxy server using start-proxy.sh."""
    script = BASE_DIR / "start-proxy.sh"
    if not script.exists():
        return False, "start-proxy.sh script not found"
    try:
        res = subprocess.run([str(script)], capture_output=True, text=True, cwd=str(BASE_DIR), timeout=20)
        healthy, msg, _ = check_proxy_health()
        if healthy:
            return True, "Proxy server is running and healthy."
        else:
            return res.returncode == 0, res.stdout or res.stderr
    except Exception as e:
        return False, f"Failed to start proxy: {e}"


def stop_proxy() -> Tuple[bool, str]:
    """Stop the proxy server using stop-proxy.sh."""
    script = BASE_DIR / "stop-proxy.sh"
    if not script.exists():
        return False, "stop-proxy.sh script not found"
    try:
        res = subprocess.run([str(script)], capture_output=True, text=True, cwd=str(BASE_DIR), timeout=15)
        return True, res.stdout.strip() or "Proxy stopped."
    except Exception as e:
        return False, f"Failed to stop proxy: {e}"


def restart_proxy() -> Tuple[bool, str]:
    """Restart the proxy server."""
    stop_proxy()
    time.sleep(1)
    return start_proxy()


def get_available_models(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, api_key: str = DEFAULT_API_KEY) -> List[str]:
    """Fetch available model IDs from /v1/models."""
    url = f"http://{host}:{port}/v1/models"
    try:
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if "data" in data:
                return [m.get("id") for m in data["data"] if "id" in m]
    except Exception:
        pass
    return ["gemini-3.8-flash-high", "gemini-3.1-pro-preview", "claude-3-7-sonnet-20250219", "claude-3-5-sonnet-latest"]


def test_gemini_anthropic(model: str = "claude-3-7-sonnet-20250219", prompt: str = "Say hello from Gemini Antigravity in 5 words.") -> Dict[str, Any]:
    """Run a test prompt through Anthropic /v1/messages."""
    url = f"http://{DEFAULT_HOST}:{DEFAULT_PORT}/v1/messages"
    payload = {
        "model": model,
        "max_tokens": 100,
        "messages": [{"role": "user", "content": prompt}]
    }
    headers = {
        "Content-Type": "application/json",
        "x-api-key": DEFAULT_API_KEY,
        "anthropic-version": "2023-06-01"
    }
    start = time.time()
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=15.0) as resp:
            latency = (time.time() - start) * 1000
            data = json.loads(resp.read().decode("utf-8"))
            # Extract content text
            content_text = ""
            for item in data.get("content", []):
                if item.get("type") == "text":
                    content_text += item.get("text", "")
            return {
                "success": True,
                "text": content_text.strip() or "(no text)",
                "latency_ms": round(latency, 1),
                "model": data.get("model", model),
                "usage": data.get("usage", {}),
                "raw": data
            }
    except urllib.error.HTTPError as e:
        latency = (time.time() - start) * 1000
        err_body = e.read().decode("utf-8", errors="replace")
        return {"success": False, "error": f"HTTP {e.code}: {err_body}", "latency_ms": round(latency, 1)}
    except Exception as e:
        latency = (time.time() - start) * 1000
        return {"success": False, "error": str(e), "latency_ms": round(latency, 1)}


def test_gemini_openai(model: str = "gemini-3.8-flash-high", prompt: str = "Say 'Hermes ready' in 3 words.") -> Dict[str, Any]:
    """Run a test prompt through OpenAI /v1/chat/completions."""
    url = f"http://{DEFAULT_HOST}:{DEFAULT_PORT}/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEFAULT_API_KEY}"
    }
    start = time.time()
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=15.0) as resp:
            latency = (time.time() - start) * 1000
            data = json.loads(resp.read().decode("utf-8"))
            content_text = ""
            choices = data.get("choices", [])
            if choices:
                content_text = choices[0].get("message", {}).get("content", "")
            return {
                "success": True,
                "text": content_text.strip() or "(no text)",
                "latency_ms": round(latency, 1),
                "model": data.get("model", model),
                "usage": data.get("usage", {}),
                "raw": data
            }
    except urllib.error.HTTPError as e:
        latency = (time.time() - start) * 1000
        err_body = e.read().decode("utf-8", errors="replace")
        return {"success": False, "error": f"HTTP {e.code}: {err_body}", "latency_ms": round(latency, 1)}
    except Exception as e:
        latency = (time.time() - start) * 1000
        return {"success": False, "error": str(e), "latency_ms": round(latency, 1)}


def get_recent_logs(lines: int = 50) -> List[str]:
    """Return the last N lines of proxy.log."""
    if not LOG_PATH.exists():
        return ["(No log file found yet)"]
    try:
        all_lines = LOG_PATH.read_text(errors="replace").splitlines()
        return all_lines[-lines:] if len(all_lines) > lines else all_lines
    except Exception as e:
        return [f"Error reading logs: {e}"]


def update_default_target_model(new_model: str) -> Tuple[bool, str]:
    """Update the default target model name in config.yaml."""
    if not CONFIG_PATH.exists():
        return False, "config.yaml not found"
    try:
        lines = CONFIG_PATH.read_text().splitlines()
        new_lines = []
        in_model_alias = False
        updated_count = 0
        for line in lines:
            if "model-alias:" in line:
                in_model_alias = True
                new_lines.append(line)
            elif in_model_alias and line.strip().startswith("- name:"):
                indent = line[:line.find("- name:")]
                new_lines.append(f'{indent}- name: "{new_model}"')
                updated_count += 1
            else:
                new_lines.append(line)

        CONFIG_PATH.write_text("\n".join(new_lines) + "\n")
        return True, f"Updated {updated_count} alias mappings to '{new_model}'."
    except Exception as e:
        return False, f"Failed to update config.yaml: {e}"


def get_agent_connection_info(tool: str) -> Dict[str, Any]:
    """
    Returns connection environment variables, launch scripts, and config snippets
    for various agent tools: OpenCode, Hermes, Claude Code, Aider, Cline, etc.
    """
    tool_key = tool.lower().strip()
    base_url_anthropic = f"http://{DEFAULT_HOST}:{DEFAULT_PORT}"
    base_url_openai = f"http://{DEFAULT_HOST}:{DEFAULT_PORT}/v1"
    key = DEFAULT_API_KEY

    info = {
        "name": tool,
        "env": {},
        "commands": [],
        "snippet": "",
        "description": ""
    }

    if tool_key in ["opencode", "open-code"]:
        info["name"] = "OpenCode"
        info["description"] = "Open-source terminal-based AI coding assistant."
        info["env"] = {
            "OPENAI_BASE_URL": base_url_openai,
            "OPENAI_API_KEY": key,
            "ANTHROPIC_BASE_URL": base_url_anthropic,
            "ANTHROPIC_API_KEY": key,
            "OPENCODE_MODEL": "antigravity/gemini-3.8-flash-high"
        }
        info["commands"] = [
            "./run-opencode.sh",
            "opencode -m antigravity/gemini-3.8-flash-high"
        ]
        info["snippet"] = (
            "# Run OpenCode with Antigravity Gemini:\n"
            "./run-opencode.sh\n\n"
            "# Or invoke opencode directly with the provider model:\n"
            "opencode -m antigravity/gemini-3.8-flash-high\n\n"
            "# Configured in ~/.config/opencode/opencode.json under 'antigravity':\n"
            "#   baseURL: http://127.0.0.1:8317/v1\n"
            "#   npm: @ai-sdk/openai-compatible\n"
            "#   apiKey: sk-antigravity-claude"
        )

    elif tool_key in ["hermes", "hermes-agent", "nous-hermes"]:
        info["name"] = "Hermes Agent"
        info["description"] = "Autonomous agent framework supporting tool use and multi-step reasoning."
        info["env"] = {
            "OPENAI_BASE_URL": base_url_openai,
            "OPENAI_API_KEY": key,
            "MODEL": "gemini-3.8-flash-high"
        }
        info["commands"] = [
            f'export OPENAI_BASE_URL="{base_url_openai}"',
            f'export OPENAI_API_KEY="{key}"',
            'hermes --model gemini-3.8-flash-high'
        ]
        info["snippet"] = (
            "# Hermes Agent Environment Setup\n"
            f"export OPENAI_BASE_URL=\"{base_url_openai}\"\n"
            f"export OPENAI_API_KEY=\"{key}\"\n"
            "export MODEL=\"gemini-3.8-flash-high\"\n\n"
            "# Run Hermes\n"
            "hermes"
        )

    elif tool_key in ["claude", "claude-code"]:
        info["name"] = "Claude Code"
        info["description"] = "Anthropic's official terminal coding agent."
        info["env"] = {
            "ANTHROPIC_BASE_URL": base_url_anthropic,
            "ANTHROPIC_API_KEY": key
        }
        info["commands"] = [
            f'export ANTHROPIC_BASE_URL="{base_url_anthropic}"',
            f'export ANTHROPIC_API_KEY="{key}"',
            'claude'
        ]
        info["snippet"] = (
            "# Claude Code Environment Setup\n"
            f"export ANTHROPIC_BASE_URL=\"{base_url_anthropic}\"\n"
            f"export ANTHROPIC_API_KEY=\"{key}\"\n"
            "claude\n\n"
            "# Or run via the included helper script:\n"
            "./run-claude.sh"
        )

    elif tool_key in ["aider", "aider-chat"]:
        info["name"] = "Aider"
        info["description"] = "Pair programming in your terminal."
        info["env"] = {
            "OPENAI_API_BASE": base_url_openai,
            "OPENAI_API_KEY": key
        }
        info["commands"] = [
            f'aider --openai-api-base "{base_url_openai}" --openai-api-key "{key}" --model openai/gemini-3.8-flash-high'
        ]
        info["snippet"] = (
            "# Aider with Antigravity Gemini via OpenAI format:\n"
            f"aider --openai-api-base \"{base_url_openai}\" \\\n"
            f"      --openai-api-key \"{key}\" \\\n"
            "      --model openai/gemini-3.8-flash-high"
        )

    elif tool_key in ["cline", "roo-code", "roocode"]:
        info["name"] = "Cline / Roo Code (VS Code)"
        info["description"] = "VS Code autonomous coding extensions."
        info["env"] = {}
        info["commands"] = []
        info["snippet"] = (
            "// Settings for Cline or Roo Code:\n"
            "// Option 1: OpenAI Compatible Provider\n"
            "{\n"
            f'  "apiProvider": "openai-compatible",\n'
            f'  "openAiBaseUrl": "{base_url_openai}",\n'
            f'  "openAiApiKey": "{key}",\n'
            f'  "openAiModelId": "gemini-3.8-flash-high"\n'
            "}\n\n"
            "// Option 2: Anthropic Provider\n"
            "{\n"
            f'  "apiProvider": "anthropic",\n'
            f'  "anthropicBaseUrl": "{base_url_anthropic}",\n'
            f'  "anthropicApiKey": "{key}",\n'
            f'  "anthropicModelId": "claude-3-7-sonnet-20250219"\n'
            "}"
        )

    elif tool_key in ["continue", "continue.dev"]:
        info["name"] = "Continue.dev"
        info["description"] = "Open-source AI code assistant for VS Code and JetBrains."
        info["env"] = {}
        info["commands"] = []
        info["snippet"] = (
            "// In ~/.continue/config.json:\n"
            '{\n'
            '  "models": [\n'
            '    {\n'
            '      "title": "Antigravity Gemini",\n'
            '      "provider": "openai",\n'
            '      "model": "gemini-3.8-flash-high",\n'
            f'      "apiBase": "{base_url_openai}",\n'
            f'      "apiKey": "{key}"\n'
            '    }\n'
            '  ]\n'
            '}'
        )

    elif tool_key in ["goose"]:
        info["name"] = "Goose AI Agent"
        info["description"] = "Open-source developer agent by Block."
        info["env"] = {
            "OPENAI_BASE_URL": base_url_openai,
            "OPENAI_API_KEY": key,
            "GOOSE_PROVIDER": "openai",
            "GOOSE_MODEL": "gemini-3.8-flash-high"
        }
        info["commands"] = [
            f'export OPENAI_BASE_URL="{base_url_openai}"',
            f'export OPENAI_API_KEY="{key}"',
            'goose session'
        ]
        info["snippet"] = (
            "# Goose Agent Environment Configuration:\n"
            f"export OPENAI_BASE_URL=\"{base_url_openai}\"\n"
            f"export OPENAI_API_KEY=\"{key}\"\n"
            "export GOOSE_PROVIDER=\"openai\"\n"
            "export GOOSE_MODEL=\"gemini-3.8-flash-high\"\n\n"
            "# Start Goose Session:\n"
            "goose session"
        )

    elif tool_key in ["droid"]:
        info["name"] = "Droid Agent"
        info["description"] = "Factory AI autonomous development agent."
        info["env"] = {
            "OPENAI_BASE_URL": base_url_openai,
            "OPENAI_API_KEY": key,
            "ANTHROPIC_BASE_URL": base_url_anthropic,
            "ANTHROPIC_API_KEY": key
        }
        info["commands"] = [
            f'export OPENAI_BASE_URL="{base_url_openai}"',
            f'export OPENAI_API_KEY="{key}"',
            'droid'
        ]
        info["snippet"] = (
            "# Droid Agent Configuration:\n"
            f"export OPENAI_BASE_URL=\"{base_url_openai}\"\n"
            f"export OPENAI_API_KEY=\"{key}\"\n"
            "droid"
        )

    elif tool_key in ["python", "langchain", "crewai"]:
        info["name"] = "Python SDK / LangChain / CrewAI"
        info["description"] = "Integration for custom AI agents and Python scripts."
        info["env"] = {}
        info["commands"] = []
        info["snippet"] = (
            "# Using official OpenAI client:\n"
            "from openai import OpenAI\n\n"
            f"client = OpenAI(base_url=\"{base_url_openai}\", api_key=\"{key}\")\n"
            "response = client.chat.completions.create(\n"
            "    model=\"gemini-3.8-flash-high\",\n"
            "    messages=[{\"role\": \"user\", \"content\": \"Hello!\"}]\n"
            ")\n"
            "print(response.choices[0].message.content)\n\n"
            "# Using official Anthropic client:\n"
            "import anthropic\n\n"
            f"client = anthropic.Anthropic(base_url=\"{base_url_anthropic}\", api_key=\"{key}\")\n"
            "message = client.messages.create(\n"
            "    model=\"claude-3-7-sonnet-20250219\",\n"
            "    max_tokens=1024,\n"
            "    messages=[{\"role\": \"user\", \"content\": \"Hello!\"}]\n"
            ")\n"
            "print(message.content[0].text)"
        )

    return info


def configure_opencode(set_default: bool = False, local_dir: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Configure OpenCode to recognize Antigravity Gemini proxy.
    Updates ~/.config/opencode/opencode.json and optionally a local opencode.json.
    """
    target_path = (local_dir / "opencode.json") if local_dir else (Path.home() / ".config" / "opencode" / "opencode.json")
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        if target_path.exists():
            try:
                data = json.loads(target_path.read_text())
            except Exception:
                data = {}

        if "provider" not in data or not isinstance(data["provider"], dict):
            data["provider"] = {}

        data["provider"]["antigravity"] = {
            "name": "Antigravity Gemini",
            "npm": "@ai-sdk/openai-compatible",
            "options": {
                "apiKey": DEFAULT_API_KEY,
                "baseURL": f"http://{DEFAULT_HOST}:{DEFAULT_PORT}/v1"
            },
            "models": {
                "gemini-3.8-flash-high": {
                    "name": "Gemini 3.8 Flash High"
                },
                "gemini-3.1-pro-preview": {
                    "name": "Gemini 3.1 Pro Preview"
                },
                "claude-3-7-sonnet-20250219": {
                    "name": "Claude 3.7 Sonnet (Gemini)"
                },
                "claude-3-5-sonnet-latest": {
                    "name": "Claude 3.5 Sonnet (Gemini)"
                }
            }
        }

        if set_default:
            data["model"] = "antigravity/gemini-3.8-flash-high"

        target_path.write_text(json.dumps(data, indent=2))
        return True, f"Successfully configured OpenCode in {target_path}"
    except Exception as e:
        return False, f"Failed to configure OpenCode: {e}"


def export_agent_env(tool: str, target_file: Optional[str] = None) -> str:
    """Export environment variables for a given agent tool to a .env file."""
    info = get_agent_connection_info(tool)
    filename = target_file or f".env.{tool.lower().replace(' ', '_')}"
    filepath = BASE_DIR / filename
    lines = [
        f"# Environment config for {info['name']}",
        f"# Generated automatically by Antigravity Gemini Proxy TUI",
        f"# Date: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        ""
    ]
    for k, v in info["env"].items():
        lines.append(f'export {k}="{v}"')
    lines.append("")
    filepath.write_text("\n".join(lines))
    return str(filepath)


def create_agent_launcher(tool: str) -> str:
    """Generate an executable bash launcher script for the requested tool."""
    tool_key = tool.lower().strip()
    script_name = f"run-{tool_key}.sh"
    script_path = BASE_DIR / script_name

    info = get_agent_connection_info(tool)
    lines = [
        "#!/usr/bin/env bash",
        f"# ==============================================================================",
        f"# Launcher for {info['name']} via Antigravity Gemini Proxy",
        f"# ==============================================================================",
        "set -euo pipefail",
        "",
        'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"',
        "",
        "# Ensure proxy is running",
        'if ! curl -s "http://127.0.0.1:8317/" > /dev/null 2>&1; then',
        '    echo "Antigravity Proxy is not running. Starting proxy first..."',
        '    "${SCRIPT_DIR}/start-proxy.sh"',
        "fi",
        "",
        "# Export connection parameters"
    ]
    for k, v in info["env"].items():
        lines.append(f'export {k}="{v}"')

    lines.append("")
    lines.append(f'echo "Starting {info["name"]} connected to Antigravity Proxy..."')

    if tool_key in ["opencode", "open-code"]:
        lines.append('if command -v opencode >/dev/null 2>&1; then')
        lines.append('    exec opencode "$@"')
        lines.append('elif command -v npx >/dev/null 2>&1; then')
        lines.append('    exec npx opencode "$@"')
        lines.append('else')
        lines.append('    echo "Error: opencode command not found. Install it via: npm i -g opencode"')
        lines.append('    exit 1')
        lines.append('fi')
    elif tool_key in ["hermes", "hermes-agent"]:
        lines.append('if command -v hermes >/dev/null 2>&1; then')
        lines.append('    exec hermes "$@"')
        lines.append('else')
        lines.append('    echo "Error: hermes command not found."')
        lines.append('    echo "Make sure hermes is installed in your python environment (e.g. pip install hermes-agent)"')
        lines.append('    exit 1')
        lines.append('fi')
    elif tool_key in ["aider"]:
        lines.append('if command -v aider >/dev/null 2>&1; then')
        lines.append('    exec aider --openai-api-base "http://127.0.0.1:8317/v1" --openai-api-key "sk-antigravity-claude" --model openai/gemini-3.8-flash-high "$@"')
        lines.append('else')
        lines.append('    echo "Error: aider command not found. Install via: pip install aider-chat"')
        lines.append('    exit 1')
        lines.append('fi')
    else:
        lines.append('echo "Configured environment variables:"')
        for k in info["env"]:
            lines.append(f'echo "  {k}=${k}"')
        lines.append('echo "Ready to launch your agent."')

    script_path.write_text("\n".join(lines))
    script_path.chmod(0o755)
    return str(script_path)
