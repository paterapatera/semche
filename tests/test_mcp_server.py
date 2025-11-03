"""Tests for MCP server functionality."""


from semche.mcp_server import hello, mcp, put_document


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


# Tests for put_document tool


def test_put_document_success(tmp_path):
    """Test successful document registration."""
    result = put_document(
        text="これはテストドキュメントです。",
        filepath="/test/doc1.md",
        file_type="test"
    )
    
    assert result["status"] == "success"
    assert result["message"] == "ドキュメントを登録しました"
    assert result["details"]["count"] == 1
    assert result["details"]["collection"] == "documents"
    assert result["details"]["filepath"] == "/test/doc1.md"
    assert result["details"]["vector_dimension"] == 768
    assert result["details"]["normalized"] is False


def test_put_document_with_normalize():
    """Test document registration with normalization."""
    result = put_document(
        text="正規化テスト",
        filepath="/test/doc_normalized.md",
        normalize=True
    )
    
    assert result["status"] == "success"
    assert result["details"]["normalized"] is True


def test_put_document_without_file_type():
    """Test document registration without file_type."""
    result = put_document(
        text="ファイルタイプなしのテスト",
        filepath="/test/doc_no_type.md"
    )
    
    assert result["status"] == "success"
    assert result["details"]["filepath"] == "/test/doc_no_type.md"


def test_put_document_upsert():
    """Test document update (upsert) with same filepath."""
    filepath = "/test/doc_upsert.md"
    
    # 初回登録
    result1 = put_document(
        text="初回のテキスト",
        filepath=filepath,
        file_type="v1"
    )
    assert result1["status"] == "success"
    
    # 同じfilepathで更新
    result2 = put_document(
        text="更新後のテキスト",
        filepath=filepath,
        file_type="v2"
    )
    assert result2["status"] == "success"


def test_put_document_empty_text():
    """Test error handling for empty text."""
    result = put_document(
        text="",
        filepath="/test/empty.md"
    )
    
    assert result["status"] == "error"
    assert result["error_type"] == "ValidationError"
    assert "空" in result["message"]


def test_put_document_whitespace_only_text():
    """Test error handling for whitespace-only text."""
    result = put_document(
        text="   \n\t  ",
        filepath="/test/whitespace.md"
    )
    
    assert result["status"] == "error"
    assert result["error_type"] == "ValidationError"


def test_put_document_empty_filepath():
    """Test error handling for empty filepath."""
    result = put_document(
        text="有効なテキスト",
        filepath=""
    )
    
    assert result["status"] == "error"
    assert result["error_type"] == "ValidationError"
    assert "filepath" in result["message"]


def test_put_document_multiple_calls():
    """Test multiple document registrations."""
    filepaths = ["/test/multi1.md", "/test/multi2.md", "/test/multi3.md"]
    texts = ["ドキュメント1", "ドキュメント2", "ドキュメント3"]
    
    for fp, txt in zip(filepaths, texts):
        result = put_document(text=txt, filepath=fp, file_type="multi")
        assert result["status"] == "success"

