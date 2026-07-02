import argparse

# CRITICAL: import camoufox BEFORE entering asyncio event loop.
# camoufox/__init__.py imports playwright.sync_api at top level.
# If that import happens inside a running asyncio loop (e.g. when
# launch_browser lazily triggers `from camoufox.async_api import ...`),
# Playwright's sync bootstrap deadlocks for 60s+.
# Pre-importing here ensures the module is cached in sys.modules
# before FastMCP starts its event loop.
import camoufox  # noqa: F401

from .server import mcp
from ._playwright_patch import patch_playwright_pageerror


def main():
    # Fix the Playwright Firefox-driver pageError crash (issue #5) before the
    # browser is ever launched. No-op on Playwright versions without the bug.
    patch_playwright_pageerror()

    parser = argparse.ArgumentParser(description="Camoufox Reverse Engineering MCP Server")
    parser.add_argument("--proxy", type=str, help="Proxy server URL (e.g. http://127.0.0.1:7890)")
    parser.add_argument("--proxy-username", type=str, help="Proxy username")
    parser.add_argument("--proxy-password", type=str, help="Proxy password")
    parser.add_argument("--proxy-bypass", type=str,
                        help="Comma-separated proxy bypass list, e.g. .example.com,localhost")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--os", type=str, default="auto",
                        choices=["auto", "windows", "macos", "linux"],
                        help="OS fingerprint to emulate (default: auto-detect host OS)")
    parser.add_argument("--locale", type=str, default="auto",
                        help="Browser locale, e.g. zh-CN, en-US (default: auto-detect)")
    parser.add_argument("--geoip", action="store_true", help="Enable GeoIP inference from proxy")
    parser.add_argument("--geoip-ip", type=str,
                        help="Use an explicit IP address for GeoIP instead of auto-detecting through the proxy")
    parser.add_argument("--humanize", action="store_true", help="Enable humanized mouse movement")
    parser.add_argument("--block-images", action="store_true", help="Block image loading")
    parser.add_argument("--block-webrtc", action="store_true", help="Block WebRTC")
    parser.add_argument("--virtual-display", type=str,
                        help="X display to use for headed browser mode, e.g. :99")
    parser.add_argument("--executable-path", type=str,
                        help="Custom Camoufox executable path")
    args = parser.parse_args()

    from .browser import BrowserManager
    from .proxy import build_proxy_config

    try:
        proxy_config = build_proxy_config(
            args.proxy,
            username=args.proxy_username,
            password=args.proxy_password,
            bypass=args.proxy_bypass,
        )
    except ValueError as exc:
        parser.error(str(exc))

    BrowserManager.default_config = {
        "proxy": proxy_config,
        "headless": args.headless,
        "os": args.os,
        "locale": args.locale,
        "geoip": args.geoip_ip or args.geoip,
        "humanize": args.humanize,
        "block_images": args.block_images,
        "block_webrtc": args.block_webrtc,
        "virtual_display": args.virtual_display,
        "executable_path": args.executable_path,
    }

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
