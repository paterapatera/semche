"""Tests for MCP server functionality."""

import pytest

from semche.mcp_server import mcp, hello


def test_mcp_server_exists():
    """Test that the MCP server instance exists."""
    assert mcp is not None
    assert mcp.name == "semche"


def test_hello_with_name():
    """Test hello function with a name parameter."""
    result = hello(name="Alice")
    assert result == "Hello, Alice!"


def test_hello_without_name():
    """Test hello function without a name parameter (should default to World)."""
    result = hello()
    assert result == "Hello, World!"


def test_hello_with_custom_name():
    """Test hello function with various custom names."""
    assert hello(name="Bob") == "Hello, Bob!"
    assert hello(name="日本語") == "Hello, 日本語!"
    assert hello(name="") == "Hello, !"
