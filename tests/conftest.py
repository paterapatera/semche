import uuid

import pytest


@pytest.fixture(autouse=True)
def _isolate_chroma_dir(tmp_path, monkeypatch):
    """Isolate ChromaDB persistence per test to avoid cross-test contamination.

    Sets SEMCHE_CHROMA_DIR to a unique temporary directory for each test.
    Tests that explicitly pass persist_directory will override this.
    """
    unique_dir = tmp_path / f"chroma_db_{uuid.uuid4().hex}"
    unique_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("SEMCHE_CHROMA_DIR", str(unique_dir))
    yield
    # No explicit cleanup required; tmp_path is ephemeral per test
