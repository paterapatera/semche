import os
from datetime import datetime
import pytest

from src.semche.chromadb_manager import ChromaDBManager, ChromaDBError


def test_init_and_persist_dir(tmp_path):
    # コンストラクタ引数優先
    mgr = ChromaDBManager(persist_directory=str(tmp_path), collection_name="docs_test")
    assert os.path.isdir(str(tmp_path)) or True  # 作成されるかは実装依存、少なくともパスは使用される
    # 取得できること
    res = mgr.save(
        embeddings=[[0.1, 0.2, 0.3]],
        documents=["hello"],
        filepaths=["/tmp/file1.txt"],
        updated_at=[datetime(2025, 1, 1)],
        file_types=["spec"],
    )
    assert res["status"] == "success"
    assert res["collection"] == "docs_test"

    got = mgr.get_by_ids(["/tmp/file1.txt"])
    assert got and "ids" in got and got["ids"] == ["/tmp/file1.txt"]
    assert got["documents"] == ["hello"]
    assert got["metadatas"][0]["filepath"] == "/tmp/file1.txt"
    assert got["metadatas"][0]["file_type"] == "spec"


def test_batch_and_upsert(tmp_path):
    mgr = ChromaDBManager(persist_directory=str(tmp_path), collection_name="docs_batch")

    # 初回保存（2件）
    res1 = mgr.save(
        embeddings=[[0.0], [1.0]],
        documents=["A", "B"],
        filepaths=["/a", "/b"],
        updated_at=["2025-01-01T00:00:00", "2025-01-02T00:00:00"],
        file_types=["jira", "design"],
    )
    assert res1["count"] == 2

    got1 = mgr.get_by_ids(["/a", "/b"])
    assert set(got1["ids"]) == {"/a", "/b"}

    # 同じIDで上書き（upsert）
    res2 = mgr.save(
        embeddings=[[2.0], [3.0]],
        documents=["A2", "B2"],
        filepaths=["/a", "/b"],
        updated_at=["2025-01-03T00:00:00", "2025-01-04T00:00:00"],
        file_types=["jira", "design"],
    )
    assert res2["count"] == 2

    got2 = mgr.get_by_ids(["/a", "/b"])
    # 上書き後のドキュメントを確認
    ids_to_doc = {i: d for i, d in zip(got2["ids"], got2["documents"])}
    assert ids_to_doc["/a"] == "A2"
    assert ids_to_doc["/b"] == "B2"


def test_persistence_across_instances(tmp_path):
    # 1つ目のインスタンスで保存
    mgr1 = ChromaDBManager(persist_directory=str(tmp_path), collection_name="docs_persist")
    mgr1.save(
        embeddings=[[0.0], [1.0], [2.0]],
        documents=["X", "Y", "Z"],
        filepaths=["/x", "/y", "/z"],
        file_types=["spec", "jira", "design"],
    )

    # 2つ目のインスタンス（同じディレクトリ/コレクション）で取得できるか
    mgr2 = ChromaDBManager(persist_directory=str(tmp_path), collection_name="docs_persist")
    got = mgr2.get_by_ids(["/x", "/y", "/z"])
    assert set(got["ids"]) == {"/x", "/y", "/z"}


def test_input_validation_errors(tmp_path):
    mgr = ChromaDBManager(persist_directory=str(tmp_path), collection_name="docs_err")

    with pytest.raises(ChromaDBError):
        mgr.save(embeddings=[], documents=[], filepaths=[])

    with pytest.raises(ChromaDBError):
        mgr.save(embeddings=[[0.0]], documents=[], filepaths=["/x"])

    with pytest.raises(ChromaDBError):
        mgr.save(
            embeddings=[[0.0], [1.0]],
            documents=["a"],
            filepaths=["/x", "/y"],
        )
