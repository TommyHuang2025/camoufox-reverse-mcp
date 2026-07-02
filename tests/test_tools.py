import os
import pytest
from camoufox_reverse_mcp.utils.js_helpers import render_trace_template
from camoufox_reverse_mcp.utils.response_fmt import format_response, truncate_str


def test_render_trace_template():
    js = render_trace_template(
        function_path="window.encrypt",
        max_captures=10,
        log_args=True,
        log_return=False,
        log_stack=True,
    )
    assert "window.encrypt" in js
    assert "10" in js
    assert "true" in js


def test_render_trace_template_defaults():
    js = render_trace_template(function_path="JSON.stringify")
    assert "JSON.stringify" in js
    assert "50" in js


def test_format_response_dict():
    result = format_response({"key": "value"})
    assert '"key"' in result
    assert '"value"' in result


def test_format_response_truncation():
    data = "x" * 100000
    result = format_response(data, max_length=100)
    assert "truncated" in result


def test_truncate_str_short():
    assert truncate_str("hello", 10) == "hello"


def test_truncate_str_long():
    result = truncate_str("a" * 100, 50)
    assert len(result) < 100
    assert "chars total" in result


def test_render_persistent_trace_template():
    from camoufox_reverse_mcp.utils.js_helpers import render_persistent_trace_template
    js = render_persistent_trace_template(
        function_path="XMLHttpRequest.prototype.open",
        max_captures=20,
        log_args=True,
        log_return=True,
        log_stack=True,
    )
    assert "XMLHttpRequest.prototype.open" in js
    assert "__MCP_TRACE__" in js
    assert "20" in js


def test_hook_files_exist():
    hooks_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "src", "camoufox_reverse_mcp", "hooks"
    )
    expected_files = [
        "xhr_hook.js",
        "fetch_hook.js",
        "crypto_hook.js",
        "websocket_hook.js",
        "debugger_trap.js",
        "trace_template.js",
        "trace_persistent_template.js",
        "property_access_hook.js",
        "jsvmp_hook.js",
    ]
    for f in expected_files:
        assert os.path.exists(os.path.join(hooks_dir, f)), f"Missing hook file: {f}"


def test_list_control_files_ignores_stale_pids(tmp_path, monkeypatch):
    from camoufox_reverse_mcp import property_trace

    monkeypatch.setattr(property_trace, "CONTROL_DIR", tmp_path)
    stale = tmp_path / "control-999999999.cmd"
    stale.write_text("on")

    files = property_trace.list_control_files(live_only=True, cleanup_stale=True)

    assert files == []
    assert not stale.exists()


@pytest.mark.asyncio
async def test_check_environment_reports_configured_runtime(tmp_path):
    """check_environment should report a configured project-local runtime."""
    from camoufox_reverse_mcp.tools import environment

    exe = tmp_path / "camoufox-bin"
    exe.write_text("#!/bin/sh\n")

    old_config = dict(environment.browser_manager.default_config)
    try:
        environment.browser_manager.default_config = {"executable_path": str(exe)}
        result = await environment.check_environment()
    finally:
        environment.browser_manager.default_config = old_config

    runtime = result["camoufox_reverse"]
    assert runtime["configured_executable"] == str(exe)
    assert runtime["configured_executable_exists"] is True
    assert runtime["installed"] is True
