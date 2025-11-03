from semche.mcp_server import delete_document, put_document
from src.semche.chromadb_manager import ChromaDBManager


def test_delete_existing_document():
    # まず登録
    filepath = "/tests/delete_me.md"
    put_document(text="削除テスト", filepath=filepath, file_type="tmp")

    # 削除実行
    res = delete_document(filepath=filepath)
    assert res["status"] == "success"
    assert res["deleted_count"] == 1

    # 実際に存在しないことを確認
    mgr = ChromaDBManager()
    got = mgr.get_by_ids([filepath])
    assert got.get("ids") == [] or got.get("ids") is None


def test_delete_nonexistent_document():
    filepath = "/tests/not_exists_12345.md"
    res = delete_document(filepath=filepath)
    assert res["status"] == "success"
    assert res["deleted_count"] == 0
    assert "見つかりません" in res["message"]


essential_error_keys = {"status", "message", "error_type"}

def test_delete_validation_error():
    res = delete_document(filepath="")
    assert res["status"] == "error"
    assert res["error_type"] == "ValidationError"
    assert all(k in res for k in essential_error_keys)
