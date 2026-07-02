import pytest
from camoufox_reverse_mcp.browser import BrowserManager, detect_system_locale, validate_browser_proxy_config
from camoufox_reverse_mcp.proxy import build_proxy_config, redact_proxy_config, redact_proxy_text


def test_browser_manager_init():
    mgr = BrowserManager()
    assert mgr.browser is None
    assert mgr.active_page_name is None
    assert len(mgr.contexts) == 0
    assert len(mgr.pages) == 0
    assert mgr._capturing is False


def test_default_config():
    assert isinstance(BrowserManager.default_config, dict)


def test_detect_system_locale_falls_back_for_c_utf8(monkeypatch):
    monkeypatch.setenv("LC_ALL", "C.UTF-8")
    monkeypatch.setenv("LC_MESSAGES", "C.utf8")
    monkeypatch.setenv("LANG", "C")

    assert detect_system_locale() == "en-US"


def test_detect_system_locale_normalizes_region(monkeypatch):
    monkeypatch.delenv("LC_ALL", raising=False)
    monkeypatch.delenv("LC_MESSAGES", raising=False)
    monkeypatch.setenv("LANG", "zh_CN.UTF-8")

    assert detect_system_locale() == "zh-CN"


def test_console_logs_maxlen():
    mgr = BrowserManager()
    assert mgr._console_logs.maxlen == 2000


def test_network_requests_maxlen():
    mgr = BrowserManager()
    assert mgr._network_requests.maxlen == 2000


def test_persistent_scripts_init():
    mgr = BrowserManager()
    assert isinstance(mgr._persistent_scripts, list)
    assert len(mgr._persistent_scripts) == 0


def test_persistent_traces_init():
    mgr = BrowserManager()
    assert isinstance(mgr._persistent_traces, dict)
    assert len(mgr._persistent_traces) == 0


def test_capture_body_default():
    mgr = BrowserManager()
    assert mgr._capture_body is False


def test_init_scripts_list():
    mgr = BrowserManager()
    assert isinstance(mgr._init_scripts, list)
    assert len(mgr._init_scripts) == 0


def test_is_connected_without_browser():
    mgr = BrowserManager()
    assert mgr.is_connected() is False


def test_is_connected_uses_browser_status():
    class ClosedBrowser:
        def is_connected(self):
            return False

    mgr = BrowserManager()
    mgr.browser = ClosedBrowser()

    assert mgr.is_connected() is False


def test_build_proxy_config_accepts_common_browser_proxy_schemes():
    servers = [
        "http://127.0.0.1:7890",
        "https://proxy.example.com:8443",
        "socks4://127.0.0.1:1081",
        "socks5://127.0.0.1:1080",
    ]

    for server in servers:
        assert build_proxy_config(server) == {"server": server}


def test_build_proxy_config_adds_standard_auth_fields():
    assert build_proxy_config(
        "socks5://proxy.example.com:1080",
        username="user",
        password="pass",
        bypass=".internal,localhost",
    ) == {
        "server": "socks5://proxy.example.com:1080",
        "username": "user",
        "password": "pass",
        "bypass": ".internal,localhost",
    }


def test_build_proxy_config_extracts_embedded_url_credentials():
    assert build_proxy_config("http://user:p%40ss@proxy.example.com:8080") == {
        "server": "http://proxy.example.com:8080",
        "username": "user",
        "password": "p@ss",
    }


def test_build_proxy_config_normalizes_curl_socks_aliases():
    assert build_proxy_config("socks5h://user:pass@proxy.example.com:1080") == {
        "server": "socks5://proxy.example.com:1080",
        "username": "user",
        "password": "pass",
    }
    assert build_proxy_config("socks4a://proxy.example.com:1080") == {
        "server": "socks4://proxy.example.com:1080",
    }


def test_build_proxy_config_rejects_credential_conflict():
    with pytest.raises(ValueError, match="either in the proxy URL or separate fields"):
        build_proxy_config("http://user:pass@proxy.example.com:8080", username="other")


def test_build_proxy_config_requires_server_for_auth():
    with pytest.raises(ValueError, match="proxy server is required"):
        build_proxy_config(None, username="user")


def test_redact_proxy_config_hides_credentials():
    redacted = redact_proxy_config({
        "server": "http://proxy.example.com:8080",
        "username": "abcdef",
        "password": "secret",
    })

    assert redacted["configured"] is True
    assert redacted["server"] == "http://proxy.example.com:8080"
    assert redacted["username"] == "ab***ef"
    assert redacted["password_configured"] is True
    assert "secret" not in str(redacted)


def test_redact_proxy_text_hides_proxy_credentials():
    proxy = {
        "server": "socks5://proxy.example.com:1080",
        "username": "proxy-user",
        "password": "proxy-pass",
    }
    text = redact_proxy_text("Failed to connect to proxy: socks5://proxy-user:proxy-pass@proxy.example.com:1080", proxy)

    assert "proxy-user" not in text
    assert "proxy-pass" not in text
    assert "socks5://***:***@proxy.example.com:1080" in text


def test_validate_browser_proxy_config_rejects_authenticated_socks():
    with pytest.raises(ValueError, match="authenticated SOCKS"):
        validate_browser_proxy_config({
            "server": "socks5://proxy.example.com:1080",
            "username": "user",
            "password": "pass",
        })


def test_validate_browser_proxy_config_allows_http_auth_and_local_socks():
    validate_browser_proxy_config({
        "server": "http://proxy.example.com:8080",
        "username": "user",
        "password": "pass",
    })
    validate_browser_proxy_config({"server": "socks5://127.0.0.1:1080"})
