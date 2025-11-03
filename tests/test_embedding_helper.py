"""Tests for embedding helper functions."""

import pytest

from src.semche.embedding import EmbeddingError, ensure_single_vector


def test_ensure_single_vector_with_single():
    """Test ensure_single_vector with a single vector."""
    vec = [0.1, 0.2, 0.3, 0.4]
    result = ensure_single_vector(vec)
    assert result == vec
    assert isinstance(result, list)
    assert len(result) == 4


def test_ensure_single_vector_with_batch():
    """Test ensure_single_vector with a batch (list of vectors)."""
    batch = [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]
    result = ensure_single_vector(batch)
    assert result == [0.1, 0.2]
    assert isinstance(result, list)
    assert len(result) == 2


def test_ensure_single_vector_with_empty_list():
    """Test ensure_single_vector with an empty list."""
    with pytest.raises(EmbeddingError, match="不正な埋め込み形式です"):
        ensure_single_vector([])


def test_ensure_single_vector_with_invalid_type():
    """Test ensure_single_vector with invalid type."""
    with pytest.raises(EmbeddingError, match="不正な埋め込み形式です"):
        ensure_single_vector("invalid")  # type: ignore[arg-type]

