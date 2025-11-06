
from semche.mcp_server import put_document, search


def setup_documents():
    put_document(text="猫は可愛い動物です。", filepath="/docs/cat.txt", file_type="animal")
    put_document(text="犬は忠実なペットです。", filepath="/docs/dog.txt", file_type="animal")
    put_document(text="Pythonはプログラミング言語です。", filepath="/docs/python.txt", file_type="tech")


def test_basic_search():
    setup_documents()
    res = search(query="かわいいペット", top_k=3)
    assert res["status"] == "success"
    assert res["count"] >= 1
    # いずれかの動物系ドキュメントがヒットするはず
    paths = [r["filepath"] for r in res["results"]]
    assert any(p in paths for p in ["/docs/cat.txt", "/docs/dog.txt"]) 


essential_keys = {"filepath", "score", "metadata"}

def test_filters_and_flags():
    setup_documents()
    # file_type フィルタ
    res = search(query="プログラミング", top_k=5, file_type="tech")
    assert res["status"] == "success"
    assert all(r["metadata"].get("file_type") == "tech" for r in res["results"]) or res["count"] == 0

    # include_documents=False
    res2 = search(query="ペット", top_k=5, include_documents=False)
    assert res2["status"] == "success"
    assert all("document" not in r or r["document"] is None for r in res2["results"])


def test_validation_errors():
    assert search(query="", top_k=3)["status"] == "error"
    assert search(query="abc", top_k=0)["status"] == "error"


def test_max_content_length():
    """max_content_lengthパラメータのテスト"""
    # 長文ドキュメントを登録
    long_text = "あ" * 1000  # 1000文字
    put_document(text=long_text, filepath="/docs/long.txt", file_type="test")
    
    # デフォルト（None）: 全文取得
    res_full = search(query="あ", top_k=5, file_type="test")
    assert res_full["status"] == "success"
    for r in res_full["results"]:
        if r["filepath"] == "/docs/long.txt" and r["document"]:
            assert len(r["document"]) == 1000
            assert "..." not in r["document"]
            break
    
    # max_content_length=100: 100文字に制限
    res_limited = search(query="あ", top_k=5, file_type="test", max_content_length=100)
    assert res_limited["status"] == "success"
    for r in res_limited["results"]:
        if r["filepath"] == "/docs/long.txt" and r["document"]:
            assert len(r["document"]) == 103  # 100 + "..."
            assert r["document"].endswith("...")
            break
    
    # max_content_length=2000: 元の長さより長い制限（全文取得）
    res_large_limit = search(query="あ", top_k=5, file_type="test", max_content_length=2000)
    assert res_large_limit["status"] == "success"
    for r in res_large_limit["results"]:
        if r["filepath"] == "/docs/long.txt" and r["document"]:
            assert len(r["document"]) == 1000
            assert "..." not in r["document"]
            break
