"""Tests for sparse_encoder.py (BM25 sparse encoder)"""

import pytest

from src.semche.sparse_encoder import BM25SparseEncoder, SparseEncoderError


def test_initialization():
    """Test BM25SparseEncoder initialization"""
    encoder = BM25SparseEncoder()
    assert encoder.bm25 is None
    assert encoder.corpus_texts == []
    assert encoder.corpus_ids == []


def test_build_index_basic():
    """Test basic index building"""
    encoder = BM25SparseEncoder()

    documents = [
        "Python is a programming language",
        "JavaScript is also a programming language",
        "Machine learning uses Python",
    ]
    doc_ids = ["doc1", "doc2", "doc3"]

    result = encoder.build_index(documents, doc_ids)

    assert result["status"] == "success"
    assert result["count"] == 3
    assert encoder.bm25 is not None
    assert len(encoder.corpus_texts) == 3
    assert len(encoder.corpus_ids) == 3


def test_build_index_validation_errors():
    """Test index building validation errors"""
    encoder = BM25SparseEncoder()

    # Length mismatch
    with pytest.raises(SparseEncoderError, match="Length mismatch"):
        encoder.build_index(["doc1", "doc2"], ["id1"])

    # Empty documents
    with pytest.raises(SparseEncoderError, match="empty document list"):
        encoder.build_index([], [])


def test_search_basic():
    """Test basic BM25 search"""
    encoder = BM25SparseEncoder()

    documents = [
        "Python programming language for machine learning",
        "JavaScript is a web programming language",
        "Machine learning and artificial intelligence",
        "Deep learning with neural networks",
    ]
    doc_ids = ["doc1", "doc2", "doc3", "doc4"]

    encoder.build_index(documents, doc_ids)

    # Search for "Python"
    results = encoder.search("Python", top_k=2)

    assert len(results) <= 2
    assert results[0]["id"] == "doc1"  # Should match best
    assert "score" in results[0]
    assert results[0]["score"] > 0


def test_search_without_index():
    """Test search without building index"""
    encoder = BM25SparseEncoder()

    with pytest.raises(SparseEncoderError, match="index not built"):
        encoder.search("query")


def test_search_top_k():
    """Test top_k parameter in search"""
    encoder = BM25SparseEncoder()

    documents = [f"Document number {i}" for i in range(10)]
    doc_ids = [f"doc{i}" for i in range(10)]

    encoder.build_index(documents, doc_ids)

    # Test different top_k values
    results_3 = encoder.search("Document", top_k=3)
    results_5 = encoder.search("Document", top_k=5)

    assert len(results_3) == 3
    assert len(results_5) == 5


def test_save_and_load(tmp_path):
    """Test saving and loading BM25 index"""
    encoder1 = BM25SparseEncoder()

    documents = [
        "Python programming",
        "JavaScript coding",
        "Machine learning",
    ]
    doc_ids = ["doc1", "doc2", "doc3"]

    encoder1.build_index(documents, doc_ids)

    # Save
    save_result = encoder1.save(str(tmp_path))
    assert save_result["status"] == "success"
    assert save_result["count"] == 3

    # Check files exist
    assert (tmp_path / "bm25_index.pkl").exists()
    assert (tmp_path / "bm25_metadata.json").exists()

    # Load into new encoder
    encoder2 = BM25SparseEncoder()
    load_result = encoder2.load(str(tmp_path))

    assert load_result["status"] == "success"
    assert load_result["count"] == 3
    assert encoder2.corpus_ids == doc_ids
    assert encoder2.corpus_texts == documents

    # Search should work after loading
    results = encoder2.search("Python", top_k=1)
    assert len(results) == 1
    assert results[0]["id"] == "doc1"


def test_save_without_index(tmp_path):
    """Test saving without building index"""
    encoder = BM25SparseEncoder()

    with pytest.raises(SparseEncoderError, match="No index to save"):
        encoder.save(str(tmp_path))


def test_load_nonexistent_files(tmp_path):
    """Test loading from directory without index files"""
    encoder = BM25SparseEncoder()

    with pytest.raises(SparseEncoderError, match="not found"):
        encoder.load(str(tmp_path))


def test_add_documents():
    """Test adding documents to existing index"""
    encoder = BM25SparseEncoder()

    # Initial index
    documents1 = ["Python programming", "JavaScript coding"]
    doc_ids1 = ["doc1", "doc2"]
    encoder.build_index(documents1, doc_ids1)

    # Add more documents
    documents2 = ["Machine learning", "Deep learning"]
    doc_ids2 = ["doc3", "doc4"]
    result = encoder.add_documents(documents2, doc_ids2)

    assert result["status"] == "success"
    assert result["count"] == 4
    assert len(encoder.corpus_texts) == 4
    assert len(encoder.corpus_ids) == 4

    # Search should work with all documents
    results = encoder.search("learning", top_k=2)
    assert len(results) == 2


def test_add_documents_validation():
    """Test add_documents validation"""
    encoder = BM25SparseEncoder()

    documents = ["doc1", "doc2"]
    doc_ids = ["id1", "id2"]
    encoder.build_index(documents, doc_ids)

    # Length mismatch
    with pytest.raises(SparseEncoderError, match="Length mismatch"):
        encoder.add_documents(["new_doc"], ["id1", "id2"])


def test_custom_tokenizer():
    """Test custom tokenizer"""

    def custom_tokenizer(text: str):
        # Simple character-level tokenizer for testing
        return list(text.lower().replace(" ", ""))

    encoder = BM25SparseEncoder(tokenizer=custom_tokenizer)

    documents = ["abc", "def", "abc def"]
    doc_ids = ["doc1", "doc2", "doc3"]

    encoder.build_index(documents, doc_ids)
    results = encoder.search("abc", top_k=2)

    # Should find documents containing 'abc' characters
    assert len(results) > 0


def test_search_result_order():
    """Test that search results are ordered by score (descending)"""
    encoder = BM25SparseEncoder()

    documents = [
        "machine",
        "machine machine",
        "machine machine machine",
        "unrelated document",
    ]
    doc_ids = ["doc1", "doc2", "doc3", "doc4"]

    encoder.build_index(documents, doc_ids)

    results = encoder.search("machine", top_k=4)

    # doc3 should have highest score (3 occurrences)
    # doc2 should have second highest (2 occurrences)
    # doc1 should have third (1 occurrence)
    assert results[0]["id"] == "doc3"
    assert results[1]["id"] == "doc2"
    assert results[2]["id"] == "doc1"

    # Scores should be descending
    assert results[0]["score"] >= results[1]["score"]
    assert results[1]["score"] >= results[2]["score"]


def test_persistence_preserves_search_results(tmp_path):
    """Test that save/load preserves search results"""
    encoder1 = BM25SparseEncoder()

    documents = [
        "Python programming language",
        "JavaScript web development",
        "Machine learning with Python",
    ]
    doc_ids = ["doc1", "doc2", "doc3"]

    encoder1.build_index(documents, doc_ids)
    results1 = encoder1.search("Python", top_k=2)

    # Save and load
    encoder1.save(str(tmp_path))
    encoder2 = BM25SparseEncoder()
    encoder2.load(str(tmp_path))

    results2 = encoder2.search("Python", top_k=2)

    # Results should be identical
    assert len(results1) == len(results2)
    for r1, r2 in zip(results1, results2):
        assert r1["id"] == r2["id"]
        assert abs(r1["score"] - r2["score"]) < 0.0001  # Float comparison


def test_mecab_japanese_tokenization():
    """Test MeCab tokenizer with Japanese text"""
    encoder = BM25SparseEncoder()

    # Pure Japanese documents
    documents = [
        "機械学習は人工知能の一分野です",
        "自然言語処理を用いてテキストを分析します",
        "深層学習はニューラルネットワークを使います",
    ]
    doc_ids = ["doc1", "doc2", "doc3"]

    encoder.build_index(documents, doc_ids)

    # Search with Japanese query
    results = encoder.search("機械学習", top_k=2)

    assert len(results) > 0
    # doc1 should contain "機械学習" and rank high
    assert results[0]["id"] == "doc1"
    assert results[0]["score"] > 0


def test_mecab_mixed_language_tokenization():
    """Test MeCab tokenizer with mixed English-Japanese text"""
    encoder = BM25SparseEncoder()

    # Mixed language documents
    documents = [
        "chromadb確認のためのテスト",
        "PostgreSQLデータベースを使用する",
        "Pythonプログラミング言語",
        "確認作業を実施します",
    ]
    doc_ids = ["doc1", "doc2", "doc3", "doc4"]

    encoder.build_index(documents, doc_ids)

    # Search with English term from mixed text
    results_en = encoder.search("chromadb", top_k=2)
    assert len(results_en) > 0
    assert results_en[0]["id"] == "doc1"
    assert results_en[0]["score"] > 0

    # Search with Japanese term from mixed text
    results_ja = encoder.search("確認", top_k=2)
    assert len(results_ja) > 0
    # Both doc1 and doc4 contain "確認"
    result_ids = [r["id"] for r in results_ja]
    assert "doc1" in result_ids or "doc4" in result_ids


def test_mecab_tokenization_splits_correctly():
    """Test that MeCab correctly splits mixed English-Japanese text into tokens"""
    encoder = BM25SparseEncoder()

    # Test tokenization directly
    test_text = "chromadb確認"
    tokens = encoder.tokenizer(test_text)

    # MeCab should split this into separate tokens
    # The exact tokenization depends on MeCab's dictionary, but
    # "chromadb" and "確認" should be separate tokens
    assert len(tokens) >= 2
    assert any("chromadb" in token.lower() for token in tokens)
    assert any("確認" in token for token in tokens)


def test_japanese_search_with_particles():
    """Test Japanese search with particles and various forms"""
    encoder = BM25SparseEncoder()

    documents = [
        "データベースを確認する",
        "データベースの管理",
        "確認作業",
    ]
    doc_ids = ["doc1", "doc2", "doc3"]

    encoder.build_index(documents, doc_ids)

    # Search for base word
    results = encoder.search("データベース", top_k=3)
    assert len(results) >= 2
    # doc1 and doc2 should be found
    result_ids = [r["id"] for r in results]
    assert "doc1" in result_ids
    assert "doc2" in result_ids

