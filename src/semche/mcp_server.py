"""MCP Server implementation for Semche.

This module hosts the FastMCP server instance and registers tools.
Actual tool implementations live under src.semche.tools.*
"""

from mcp.server.fastmcp import FastMCP

from semche.tools.document import put_document as _put_document_tool
from semche.tools.hello import hello as _hello_tool
from semche.tools.search import search as _search_tool

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


@mcp.tool()
def search(
    query: str,
    top_k: int = 5,
    file_type: str | None = None,
    filepath_prefix: str | None = None,
    normalize: bool = False,
    min_score: float | None = None,
    include_documents: bool = True,
) -> dict:
    """セマンティック検索（ChromaDB）。"""
    return _search_tool(
        query=query,
        top_k=top_k,
        file_type=file_type,
        filepath_prefix=filepath_prefix,
        normalize=normalize,
        min_score=min_score,
        include_documents=include_documents,
    )

