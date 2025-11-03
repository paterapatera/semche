"""MCP Server implementation for Semche.

This module hosts the FastMCP server instance and registers tools.
Actual tool implementations live under src.semche.tools.*
"""

from mcp.server.fastmcp import FastMCP

from semche.tools import hello as _hello_tool
from semche.tools import put_document as _put_document_tool


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
    return _hello_tool(name=name)


@mcp.tool()
def put_document(
    text: str,
    filepath: str,
    file_type: str = None,
    normalize: bool = False,
) -> dict:
    """テキストをベクトル化してChromaDBに保存します（upsert）。

    既存のfilepathがある場合は更新、なければ新規追加します。
    """
    return _put_document_tool(
        text=text,
        filepath=filepath,
        file_type=file_type,
        normalize=normalize,
    )

