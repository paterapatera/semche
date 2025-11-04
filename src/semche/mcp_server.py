"""MCP Server implementation for Semche.

This module hosts the FastMCP server instance and registers tools.
Actual tool implementations live under src.semche.tools.*
"""

from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from semche.tools.delete import delete_document as _delete_document_tool
from semche.tools.document import put_document as _put_document_tool
from semche.tools.search import search as _search_tool

# Create FastMCP server instance
mcp = FastMCP("semche")


@mcp.tool(
    name="put_document",
    description="テキストをベクトル化してChromaDBに保存（upsert）。既存IDは更新、未登録は新規作成。",
)
def put_document(
    text: Annotated[str, Field(description="保存するテキスト内容")],
    filepath: Annotated[str, Field(description="ドキュメントIDとして使うfilepathまたはURL")],
    file_type: Annotated[str | None, Field(description="ドキュメントの種類（任意）")] = None,
    normalize: Annotated[bool, Field(description="埋め込みベクトルを正規化するか（デフォルトFalse）")] = False,
) -> dict:
    return _put_document_tool(
        text=text,
        filepath=filepath,
        file_type=file_type,
        normalize=normalize,
    )

 


@mcp.tool(
    name="search",
    description="ハイブリッド検索（Dense+Sparse, RRF）。file_typeフィルタやドキュメント内容の返却を制御可能。",
)
def search(
    query: Annotated[str, Field(description="検索クエリ文字列")],
    top_k: Annotated[int, Field(description="取得する上位k件の数（デフォルト5、1以上を推奨）", ge=1)] = 5,
    file_type: Annotated[str | None, Field(description="メタデータのfile_typeでフィルタ（任意）")] = None,
    include_documents: Annotated[bool, Field(description="ドキュメント内容を結果に含めるか（デフォルトTrue）")] = True,
) -> dict:
    return _search_tool(
        query=query,
        top_k=top_k,
        file_type=file_type,
        include_documents=include_documents,
    )

 


@mcp.tool(
    name="delete_document",
    description="指定したfilepath(ID)のドキュメントを削除。存在しない場合もエラーにせずdeleted_count=0を返す。",
)
def delete_document(
    filepath: Annotated[str, Field(description="削除対象のドキュメントID（filepath）")]
) -> dict:
    return _delete_document_tool(filepath=filepath)

 


if __name__ == "__main__":
    # Run the MCP server on stdio
    mcp.run()
