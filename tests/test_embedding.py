import pytest
from src.semche.embedding import Embedder, EmbeddingError

@pytest.fixture(scope="module")
def embedder():
    return Embedder()

def test_single_text_embedding(embedder):
    text = "これはテストです。"
    vec = embedder.addDocument(text)
    assert isinstance(vec, list)
    assert len(vec) == 768
    assert all(isinstance(x, float) for x in vec)

def test_batch_text_embedding(embedder):
    texts = ["テスト1", "テスト2"]
    vecs = embedder.addDocument(texts)
    assert isinstance(vecs, list)
    assert len(vecs) == 2
    for v in vecs:
        assert isinstance(v, list)
        assert len(v) == 768

def test_english_text_embedding(embedder):
    text = "This is a test."
    vec = embedder.addDocument(text)
    assert isinstance(vec, list)
    assert len(vec) == 768

def test_normalize_option(embedder):
    text = "正規化テスト"
    vec = embedder.addDocument(text, normalize=True)
    norm = sum(x * x for x in vec) ** 0.5
    assert abs(norm - 1.0) < 1e-6

def test_empty_string_error(embedder):
    with pytest.raises(EmbeddingError):
        embedder.addDocument("")

def test_empty_list_error(embedder):
    with pytest.raises(EmbeddingError):
        embedder.addDocument([])

def test_invalid_input_type(embedder):
    with pytest.raises(EmbeddingError):
        embedder.addDocument(123)
