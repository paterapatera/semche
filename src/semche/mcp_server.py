"""MCP Server implementation for Semche.

This module provides a simple MCP server skeleton with a hello tool
for testing and validation purposes.
"""

from mcp.server.fastmcp import FastMCP


# Create FastMCP server instance
mcp = FastMCP("semche")


@mcp.tool()
def hello(name: str = "World") -> str:
    """Returns a greeting message.
    
    Args:
        name: Name to greet (optional, defaults to 'World')
        
    Returns:
        Greeting message in the format "Hello, {name}!"
    """
    return f"Hello, {name}!"
