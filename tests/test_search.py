
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
