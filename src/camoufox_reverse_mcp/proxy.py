from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote, unquote, urlsplit, urlunsplit


_BROWSER_PROXY_SCHEME_ALIASES = {
    "socks5h": "socks5",
    "socks4a": "socks4",
}


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def build_proxy_config(
    server: str | None,
    username: str | None = None,
    password: str | None = None,
    bypass: str | None = None,
) -> dict[str, str] | None:
    """Build a Playwright/Camoufox proxy config from MCP inputs.

    `server` keeps backwards compatibility with the old single-string API.
    If credentials are embedded in a URL such as
    `http://user:pass@example.com:8080`, they are moved into the standard
    `username` / `password` fields so Camoufox and Playwright see the normal
    proxy dictionary shape.
    """
    server = _clean(server)
    username = _clean(username)
    password = _clean(password)
    bypass = _clean(bypass)

    if not server:
        if username or password or bypass:
            raise ValueError("proxy server is required when proxy credentials or bypass are provided")
        return None

    if "://" in server:
        parsed = urlsplit(server)
        scheme = _BROWSER_PROXY_SCHEME_ALIASES.get(parsed.scheme.lower(), parsed.scheme)
        if parsed.username or parsed.password:
            if username or password:
                raise ValueError("provide proxy credentials either in the proxy URL or separate fields, not both")
            username = unquote(parsed.username or "")
            password = unquote(parsed.password or "")
            netloc = parsed.hostname or ""
            if parsed.port is not None:
                netloc = f"{netloc}:{parsed.port}"
            server = urlunsplit((scheme, netloc, parsed.path, parsed.query, parsed.fragment))
        elif scheme != parsed.scheme:
            server = urlunsplit((scheme, parsed.netloc, parsed.path, parsed.query, parsed.fragment))

    proxy: dict[str, str] = {"server": server}
    if username:
        proxy["username"] = username
    if password:
        proxy["password"] = password
    if bypass:
        proxy["bypass"] = bypass
    return proxy


def redact_text(value: str | None, visible: int = 2) -> str | None:
    if not value:
        return value
    if len(value) <= visible * 2:
        return "*" * len(value)
    return f"{value[:visible]}***{value[-visible:]}"


def redact_proxy_url(server: str | None) -> str | None:
    if not server or "://" not in server:
        return server

    parsed = urlsplit(server)
    if not parsed.username and not parsed.password:
        return server

    auth = redact_text(unquote(parsed.username or ""), visible=1) or ""
    if parsed.password:
        auth += ":***"
    host = parsed.hostname or ""
    if parsed.port is not None:
        host = f"{host}:{parsed.port}"
    return urlunsplit((parsed.scheme, f"{quote(auth, safe='*:')}@{host}", parsed.path, parsed.query, parsed.fragment))


def redact_proxy_config(proxy: dict[str, Any] | None) -> dict[str, Any]:
    if not proxy:
        return {"configured": False}

    return {
        "configured": True,
        "server": redact_proxy_url(str(proxy.get("server") or "")),
        "username": redact_text(str(proxy["username"]), visible=2) if proxy.get("username") else None,
        "password_configured": bool(proxy.get("password")),
        "bypass": proxy.get("bypass"),
    }


def redact_proxy_text(value: Any, proxy: dict[str, Any] | None = None) -> str:
    text = str(value)
    secrets: list[str] = []
    if proxy:
        for key in ("username", "password"):
            secret = proxy.get(key)
            if secret:
                secrets.append(str(secret))
                secrets.append(quote(str(secret), safe=""))
        server = proxy.get("server")
        if isinstance(server, str) and "://" in server:
            parsed = urlsplit(server)
            if parsed.username:
                secrets.append(unquote(parsed.username))
            if parsed.password:
                secrets.append(unquote(parsed.password))

    for secret in sorted(set(secrets), key=len, reverse=True):
        if secret:
            text = text.replace(secret, "***")

    return re.sub(r"([a-z][a-z0-9+.-]*://)([^:/@\s]+):([^@\s]+)@", r"\1***:***@", text, flags=re.I)
