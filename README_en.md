# camoufox-reverse-mcp

[中文](README.md) | [English](README_en.md)

> Anti-detection browser MCP server for JavaScript reverse engineering.

An MCP (Model Context Protocol) server that gives AI coding assistants (Claude Code, Cursor, Cline, etc.) the ability to perform JavaScript reverse engineering through the **Camoufox** anti-detection browser — including API parameter analysis, JS source analysis, dynamic debugging, function hooking, network interception, JSVMP bytecode analysis, and cookie/storage management.

## Why Camoufox?

| Feature | chrome-devtools-mcp | **camoufox-reverse-mcp** |
|---------|--------------------|-----------------------|
| Browser Engine | Chrome (Puppeteer) | **Firefox (Camoufox)** |
| Anti-Detection | None | **C++ engine-level fingerprint spoofing** |
| Debug Capability | Limited (no breakpoints) | **Playwright + JS Hook** |
| JSVMP Analysis | None | **Interpreter instrumentation + source-level rewriting** |
| Hook Persistence | Not supported | **Context-level persistence, auto re-inject after navigation** |

**Core Advantages:**
- Camoufox modifies fingerprint information at the **C++ engine level**, not JS patches — fundamentally undetectable
- Juggler protocol sandbox isolation makes Playwright **completely undetectable** by page JS
- BrowserForge generates fingerprints based on **real-world traffic distribution**
- Works on sites with strong bot detection: RS, AK, JY, CF, etc.
- Hooks use `Object.defineProperty` with **override protection**

---

## Quick Start

### Option 1: Install via AI Chat (Recommended)

Paste the following into your AI coding tool's chat (Cursor / Claude Code / Codex, etc.):

```
Please install this MCP tool: camoufox-reverse-mcp
Project URL: https://github.com/WhiteNightShadow/camoufox-reverse-mcp
```

The AI will automatically clone, install dependencies, and configure the MCP server.

### Option 2: Manual Installation

```bash
git clone https://github.com/WhiteNightShadow/camoufox-reverse-mcp.git
cd camoufox-reverse-mcp
pip install -e .
```

### Client Configuration

<details>
<summary><b>Cursor (.cursor/mcp.json)</b></summary>

```json
{
  "mcpServers": {
    "camoufox-reverse": {
      "command": "python",
      "args": ["-m", "camoufox_reverse_mcp"]
    }
  }
}
```

</details>

<details>
<summary><b>Claude Code</b></summary>

```json
{
  "mcpServers": {
    "camoufox-reverse": {
      "command": "python",
      "args": ["-m", "camoufox_reverse_mcp", "--headless"]
    }
  }
}
```

</details>

<details>
<summary><b>Claude Code (with proxy)</b></summary>

```json
{
  "mcpServers": {
    "camoufox-reverse": {
      "command": "python",
      "args": [
        "-m", "camoufox_reverse_mcp",
        "--proxy", "http://127.0.0.1:7890",
        "--geoip",
        "--humanize"
      ]
    }
  }
}
```

For authenticated proxies, prefer separate username/password arguments instead
of embedding credentials in the URL:

```json
{
  "mcpServers": {
    "camoufox-reverse": {
      "command": "python",
      "args": [
        "-m", "camoufox_reverse_mcp",
        "--proxy", "socks5://proxy.example.com:1080",
        "--proxy-username", "${PROXY_USERNAME}",
        "--proxy-password", "${PROXY_PASSWORD}",
        "--geoip",
        "--block-webrtc"
      ]
    }
  }
}
```

If you already obtained the proxy exit IP from a provider-specific IP echo,
avoid the extra public-IP lookup by passing it explicitly:

```json
{
  "mcpServers": {
    "camoufox-reverse": {
      "command": "python",
      "args": [
        "-m", "camoufox_reverse_mcp",
        "--proxy", "http://proxy.example.com:8080",
        "--proxy-username", "${PROXY_USERNAME}",
        "--proxy-password", "${PROXY_PASSWORD}",
        "--geoip-ip", "203.0.113.10"
      ]
    }
  }
}
```

You can also pass proxy auth for a single tool call:

```text
launch_browser(
  proxy="socks5://proxy.example.com:1080",
  proxy_username="user",
  proxy_password="pass",
  proxy_bypass=".internal,localhost",
  geoip=true
)
```

Proxy support:

| Proxy type | MCP config | Status |
|---|---|---|
| HTTP proxy | `--proxy http://host:port` | Supported |
| HTTPS proxy | `--proxy https://host:port` | Supported |
| SOCKS4 proxy | `--proxy socks4://host:port` | Forwarded to Playwright/Firefox; actual usability depends on the browser runtime |
| SOCKS5 proxy | `--proxy socks5://host:port` | Unauthenticated SOCKS5 is supported; Firefox does not support username/password auth for SOCKS5 |

Providers such as ASocks, Decodo, Proxy-Seller, and IPRoyal are supported when
they expose a normal HTTP(S) or unauthenticated SOCKS5 endpoint. Use the same
`server + username + password` fields; provider-specific country, ASN, and
sticky-session choices usually live in the provider username, password, or port.
`socks5h://` / `socks4a://` are common in curl/protocol scripts; MCP normalizes
them to `socks5://` / `socks4://` before passing the proxy to the browser.
If a provider only exports authenticated SOCKS5, run a local no-auth chain proxy
and point the browser at `socks5://127.0.0.1:<port>`.

</details>

<details>
<summary><b>Claude Code (using an existing Xvfb display)</b></summary>

When the server already has `Xvfb :99`, MCP can default to headed browser mode on that display:

```json
{
  "mcpServers": {
    "camoufox-reverse": {
      "command": "python",
      "args": [
        "-m", "camoufox_reverse_mcp",
        "--virtual-display", ":99"
      ]
    }
  }
}
```

You can also pass `launch_browser(headless=false, virtual_display=":99")` for a single tool call. Without `DISPLAY` or `virtual_display`, `headless=false` fails on Linux servers with no X display.

</details>

### Locale Auto-Detection

`launch_browser(locale="auto")` reads the system locale from `LC_ALL`, `LC_MESSAGES`, and `LANG`, then converts it to a Camoufox-compatible value such as `zh_CN.UTF-8` → `zh-CN`. If the host only has a POSIX/C locale such as `C`, `C.UTF-8`, or `POSIX`, it falls back to `en-US` so Camoufox does not fail with `Invalid locale: 'C'`.

When you need a fixed browser language, still prefer passing `launch_browser(locale="zh-CN")` explicitly or starting the MCP server with `--locale zh-CN`.

### Project-Local camoufox-reverse Runtime

If you do not want to replace the global `~/.cache/camoufox` browser, extract the custom runtime into the project and pass its binary through `--executable-path`:

```json
{
  "mcpServers": {
    "camoufox-reverse": {
      "command": "python",
      "args": [
        "-m", "camoufox_reverse_mcp",
        "--executable-path",
        "artifacts/camoufox-reverse/runtime/v135.0.1-beta.25/camoufox-bin"
      ]
    }
  }
}
```

For one tool call:

```text
launch_browser(
  enable_trace=true,
  executable_path="artifacts/camoufox-reverse/runtime/v135.0.1-beta.25/camoufox-bin"
)
```

`enable_trace=true` injects the PropertyTracer configuration and writes control/trace files under `~/.cache/camoufox-reverse/`. Then use `trace_property_access`, `list_trace_files`, and `query_trace_file`.

---

## Available Tools (35)

### Browser Control
| Tool | Description |
|------|-------------|
| `launch_browser` | Launch Camoufox anti-detection browser |
| `close_browser` | Close browser and release resources |
| `navigate` | Navigate to URL (supports pre_inject_hooks, redirect_chain tracking) |
| `reload` | Reload current page |
| `take_screenshot` | Screenshot (full page or specific element) |
| `take_snapshot` | Get accessibility tree (token-efficient) |
| `click` / `type_text` | Click element / type text |
| `wait_for` | Wait for element or URL pattern |
| `get_page_info` | Get current page URL, title, viewport |

`launch_browser` accepts `virtual_display` for Linux server headed mode, for example `virtual_display=":99"`. It is passed to Camoufox's `virtual_display` option, so the MCP process does not need an external `DISPLAY` environment variable. `executable_path` selects a project-local or custom Camoufox binary.

### JS Execution & Debugging
| Tool | Description |
|------|-------------|
| `evaluate_js` | Execute arbitrary JS in page context (multi-strategy JSON parsing) |

### Script Analysis
| Tool | Description |
|------|-------------|
| `scripts(action)` | Script management: `list` / `get` source / `save` to local file |
| `search_code` | Search keyword (`script_url=None` for all scripts, or specify URL for single-script with auto char-mode for minified files) |

### Hooking & Tracing
| Tool | Description |
|------|-------------|
| `hook_function` | Hook or trace a function: `mode="intercept"` for custom code / `mode="trace"` for non-invasive tracing |
| `inject_hook_preset` | One-click preset hooks (xhr / fetch / crypto / websocket / debugger_bypass / cookie / runtime_probe) |
| `remove_hooks` | Remove all hooks and restore original objects |
| `get_console_logs` | Get page console output |

### Network Analysis
| Tool | Description |
|------|-------------|
| `network_capture(action)` | Capture control: `start` / `stop` / `clear` / `status` |
| `list_network_requests` | List captured requests (filter by URL / domain / method / type / status) |
| `get_network_request` | Get full request details (`max_body_size` controls body truncation) |
| `get_request_initiator` | Get JS call stack that initiated a request |
| `intercept_request` | Intercept requests: log / block / modify / mock / stop |

### JSVMP Reverse Analysis

> **Anti-Bot Type → Tool Path**
>
> | Type | Examples | ✅ Recommended | ❌ Avoid |
> |---|---|---|---|
> | **Signature-based** | RS 5/6, AK sensor_data | `instrumentation(action="install")` | `pre_inject_hooks`, `hook_jsvmp_interpreter(mode="proxy")` |
> | **Behavior-based** | TK JSVMP, JY gt4 | `hook_jsvmp_interpreter(mode="proxy")` | — |
> | **Pure obfuscation** | JS obfuscation tools | Any combination | — |

| Tool | Description |
|------|-------------|
| `hook_jsvmp_interpreter` | JSVMP runtime probe (`mode="proxy"` full coverage / `mode="transparent"` signature-safe) |
| `instrumentation(action)` | Source-level instrumentation: `install` / `log` / `stop` / `reload` / `status` |
| `compare_env` | Collect browser env fingerprint for Node.js/jsdom comparison |

### Cookies & Storage
| Tool | Description |
|------|-------------|
| `cookies(action)` | Cookie management: `get` / `set` / `delete` |
| `get_storage` | Get localStorage / sessionStorage |
| `export_state` / `import_state` | Save / restore full browser state |

### Verification & Environment
| Tool | Description |
|------|-------------|
| `verify_signer_offline` | Offline signer verification: provide samples, get char-level diff at first divergence |
| `check_environment` | One-stop self-check: MCP version, dependencies, browser state |
| `reset_browser_state` | Clear residuals (hooks / capture / routes) without closing browser |

---

## Usage Scenarios

### Scenario 1: Reverse Engineer Login API Signing

```
1. launch_browser()
2. inject_hook_preset("xhr")
3. inject_hook_preset("crypto")
4. navigate("https://example.com/login")
5. type_text("#username", "test") → click("#login-btn")
6. list_network_requests(method="POST")
7. get_request_initiator(request_id=3)     ← Find signing function
8. search_code("sign")                     ← Search signing code
9. hook_function("window.getSign", mode="trace")
10. reload() → get_console_logs()          ← Collect trace data
```

### Scenario 2: Universal JSVMP Reverse (RS / AK / Custom VMP)

```
1. launch_browser()
2. network_capture(action="start")
3. navigate("https://target-site.com/")
4. list_network_requests(resource_type="script")  ← Find VMP script
5. instrumentation(action="install", url_pattern="**/vmp_target*.js", mode="ast")
6. inject_hook_preset("cookie", persistent=True)
7. instrumentation(action="reload")               ← Activate instrumentation
8. instrumentation(action="log", type_filter="tap_get")  ← See env reads
9. instrumentation(action="log", type_filter="tap_method") ← See API calls
10. compare_env()                                  ← Collect env for Node.js
```

### Scenario 3: Verify Signing Code

```
1. launch_browser() → navigate("https://target.com")
2. network_capture(action="start")
3. # Trigger target actions, collect signed requests
4. reqs = list_network_requests(url_filter="api/search")
5. # Extract samples
6. verify_signer_offline(
     signer_code="(s) => ({'X-Bogus': mySign(s.url)})",
     samples=[{"id": "r1", "input": {...}, "expected": {"X-Bogus": "..."}}]
   )
```

> 👉 Full anti-bot type identification and workflow guide: [docs/JSVMP_PLAYBOOK.md](docs/JSVMP_PLAYBOOK.md)

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│           AI Coding Assistant (Cursor / Claude)  │
│                    ↕ MCP (stdio)                 │
├─────────────────────────────────────────────────┤
│           camoufox-reverse-mcp (35 tools)        │
│  ┌──────────┬──────────┬──────────┬──────────┐  │
│  │Navigation│ Script   │Debugging │ Hooking  │  │
│  │          │ Analysis │          │          │  │
│  ├──────────┼──────────┼──────────┼──────────┤  │
│  │ Network  │ JSVMP    │  Cookie  │  Verify  │  │
│  │ Capture  │ Analysis │ Storage  │  Signer  │  │
│  └──────────┴──────────┴──────────┴──────────┘  │
│                    ↕ Playwright API               │
├─────────────────────────────────────────────────┤
│      Camoufox (Anti-detection Firefox, Juggler)  │
│  C++ engine-level fingerprint spoofing           │
└─────────────────────────────────────────────────┘
```

---

## Changelog

### v1.0.0 (2026-04-18) — Streamline + Pure JS Reverse Toolkit

> **Major release**: 80 → 32 tools, schema tokens halved. Session/assertion system removed. Pure JS reverse engineering toolkit.

**Tool Merges (v0.9.0)**
- `network_capture(action)` ← start/stop_network_capture
- `scripts(action)` ← list_scripts / get_script_source / save_script
- `search_code(keyword, script_url)` ← search_code / search_code_in_script
- `hook_function(path, mode)` ← hook_function / trace_function
- `instrumentation(action)` ← instrument_jsvmp_source / get_instrumentation_log / stop_instrumentation / reload_with_hooks / get_instrumentation_status
- `cookies(action)` ← get_cookies / set_cookies / delete_cookies

**Removed**: Session archive (7 tools), assertion system (4 tools), 37 cold tools

**Added**: `verify_signer_offline` — stateless signer verification

**Bug Fixes (v0.8.1)**: evaluate_js multi-strategy JSON parse, navigate auto-clear network buffer, get_network_request max_body_size, launch_browser residual diagnostics

**Removed dependency**: `tldextract`

### v0.6.0 — Bug Fixes
### v0.5.0 — Signature-Based Anti-Bot Compatibility
### v0.4.0 — Universal JSVMP Adaptation
### v0.3.0 — Stability Fixes
### v0.2.0 — Hook Persistence + JSVMP Analysis
### v0.1.0 — Initial Release (44 tools)

---

## Feedback / Contact

Hit a bug, want a new hook preset, or just want to chat about JS reverse engineering? Add me on WeChat:

- **WeChat ID**: `han8888v8888`

> Please note "camoufox-reverse" in your friend request.

## License

MIT
