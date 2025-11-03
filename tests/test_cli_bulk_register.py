"""Tests for CLI bulk register functionality."""

import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from semche.cli.bulk_register import (
    generate_document_id,
    is_binary_file,
    parse_date_filter,
    process_files,
    read_file_content,
    resolve_inputs,
    should_ignore,
)


class TestParseDateFilter:
    """Tests for parse_date_filter function."""

    def test_parse_yyyy_mm_dd(self):
        """Test parsing YYYY-MM-DD format."""
        result = parse_date_filter("2025-11-01")
        assert result == datetime(2025, 11, 1)

    def test_parse_iso8601_with_time(self):
        """Test parsing ISO8601 with time."""
        result = parse_date_filter("2025-11-01T12:30:45")
        assert result == datetime(2025, 11, 1, 12, 30, 45)

    def test_parse_invalid_format(self):
        """Test parsing invalid format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_filter("invalid-date")


class TestShouldIgnore:
    """Tests for should_ignore function."""

    def test_ignore_match(self):
        """Test path matching ignore pattern."""
        path = Path("/project/.git/config")
        patterns = ["**/.git/**", "**/node_modules/**"]
        assert should_ignore(path, patterns) is True

    def test_ignore_no_match(self):
        """Test path not matching ignore pattern."""
        path = Path("/project/src/main.py")
        patterns = ["**/.git/**", "**/node_modules/**"]
        assert should_ignore(path, patterns) is False

    def test_ignore_empty_patterns(self):
        """Test with empty ignore patterns."""
        path = Path("/project/file.txt")
        assert should_ignore(path, []) is False


class TestIsBinaryFile:
    """Tests for is_binary_file function."""

    def test_text_file(self, tmp_path):
        """Test text file detection."""
        text_file = tmp_path / "test.txt"
        text_file.write_text("This is a text file", encoding="utf-8")
        assert is_binary_file(text_file) is False

    def test_binary_file(self, tmp_path):
        """Test binary file detection."""
        binary_file = tmp_path / "test.bin"
        binary_file.write_bytes(b"\x00\x01\x02\x03")
        assert is_binary_file(binary_file) is True


class TestGenerateDocumentId:
    """Tests for generate_document_id function."""

    def test_absolute_path_default(self):
        """Test ID generation with absolute path (default behavior)."""
        cwd = Path("/home/user/project")
        file_path = Path("/home/user/project/docs/file.md")
        doc_id = generate_document_id(file_path, cwd, "")
        assert doc_id == "/home/user/project/docs/file.md"

    def test_absolute_path_with_prefix(self):
        """Test ID generation with absolute path and prefix."""
        cwd = Path("/home/user/project")
        file_path = Path("/home/user/project/docs/file.md")
        doc_id = generate_document_id(file_path, cwd, "myproject")
        assert doc_id == "myproject:/home/user/project/docs/file.md"

    def test_relative_path_flag(self):
        """Test ID generation with relative path flag."""
        cwd = Path("/home/user/project")
        file_path = Path("/home/user/project/docs/file.md")
        doc_id = generate_document_id(file_path, cwd, "", use_relative_path=True)
        assert doc_id == "docs/file.md"

    def test_relative_path_with_prefix(self):
        """Test ID generation with relative path flag and prefix."""
        cwd = Path("/home/user/project")
        file_path = Path("/home/user/project/docs/file.md")
        doc_id = generate_document_id(file_path, cwd, "abc", use_relative_path=True)
        assert doc_id == "abc:docs/file.md"

    def test_relative_path_outside_cwd(self):
        """Test ID generation for file outside cwd with relative path flag."""
        cwd = Path("/home/user/project")
        file_path = Path("/other/docs/file.md")
        doc_id = generate_document_id(file_path, cwd, "", use_relative_path=True)
        # Should fallback to absolute path
        assert doc_id == "/other/docs/file.md"

    def test_path_separator_consistency(self):
        """Test that path separators are always forward slashes."""
        cwd = Path("/home/user/project")
        file_path = Path("/home/user/project/docs/subdir/file.md")
        doc_id = generate_document_id(file_path, cwd, "")
        assert "\\" not in doc_id
        assert "/" in doc_id


class TestReadFileContent:
    """Tests for read_file_content function."""

    def test_read_utf8_file(self, tmp_path):
        """Test reading UTF-8 file."""
        file_path = tmp_path / "test.txt"
        content = "テストコンテンツ"
        file_path.write_text(content, encoding="utf-8")
        
        result = read_file_content(file_path)
        assert result == content

    def test_skip_empty_file(self, tmp_path):
        """Test skipping empty file."""
        file_path = tmp_path / "empty.txt"
        file_path.write_text("", encoding="utf-8")
        
        result = read_file_content(file_path)
        assert result is None

    def test_skip_whitespace_only(self, tmp_path):
        """Test skipping whitespace-only file."""
        file_path = tmp_path / "whitespace.txt"
        file_path.write_text("   \n\t  ", encoding="utf-8")
        
        result = read_file_content(file_path)
        assert result is None

    def test_skip_binary_file(self, tmp_path):
        """Test skipping binary file."""
        file_path = tmp_path / "binary.bin"
        file_path.write_bytes(b"\x00\x01\x02")
        
        result = read_file_content(file_path)
        assert result is None


class TestResolveInputs:
    """Tests for resolve_inputs function."""

    def test_resolve_single_file(self, tmp_path):
        """Test resolving single file."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("content")
        
        result = resolve_inputs([str(file1)], [], None, tmp_path)
        assert len(result) == 1
        assert result[0].name == "file1.txt"

    def test_resolve_directory(self, tmp_path):
        """Test resolving directory."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")
        
        result = resolve_inputs([str(tmp_path)], [], None, tmp_path)
        assert len(result) == 2

    def test_resolve_with_ignore(self, tmp_path):
        """Test resolving with ignore patterns."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "ignored.log"
        file1.write_text("content1")
        file2.write_text("content2")
        
        result = resolve_inputs([str(tmp_path)], ["**/*.log"], None, tmp_path)
        assert len(result) == 1
        assert result[0].name == "file1.txt"

    def test_resolve_with_date_filter(self, tmp_path):
        """Test resolving with date filter."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("content1")
        
        # Set modification time to past
        past_time = (datetime.now() - timedelta(days=10)).timestamp()
        os.utime(file1, (past_time, past_time))
        
        # Filter should exclude old files
        filter_date = datetime.now() - timedelta(days=5)
        result = resolve_inputs([str(tmp_path)], [], filter_date, tmp_path)
        assert len(result) == 0


class TestProcessFiles:
    """Tests for process_files function."""

    def test_process_single_file_absolute_path(self, tmp_path):
        """Test processing single file with absolute path (default)."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("Test content for embedding")
        
        # Mock embedder
        mock_embedder = MagicMock()
        mock_embedder.addDocument.return_value = [0.1] * 768
        
        embeddings, documents, ids, updated_at_list, file_types = process_files(
            [file1],
            tmp_path,
            "",
            "test",
            mock_embedder,
            use_relative_path=False,  # Default: absolute path
        )
        
        assert len(embeddings) == 1
        assert len(documents) == 1
        assert len(ids) == 1
        assert documents[0] == "Test content for embedding"
        # Should be absolute path
        assert ids[0] == str(file1.as_posix())
        assert file_types[0] == "test"

    def test_process_single_file_relative_path(self, tmp_path):
        """Test processing single file with relative path."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("Test content for embedding")
        
        # Mock embedder
        mock_embedder = MagicMock()
        mock_embedder.addDocument.return_value = [0.1] * 768
        
        embeddings, documents, ids, updated_at_list, file_types = process_files(
            [file1],
            tmp_path,
            "",
            "test",
            mock_embedder,
            use_relative_path=True,
        )
        
        assert len(embeddings) == 1
        assert ids[0] == "file1.txt"

    def test_process_with_prefix_absolute(self, tmp_path):
        """Test processing with ID prefix and absolute path."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("Test content")
        
        mock_embedder = MagicMock()
        mock_embedder.addDocument.return_value = [0.1] * 768
        
        embeddings, documents, ids, updated_at_list, file_types = process_files(
            [file1],
            tmp_path,
            "myprefix",
            "note",
            mock_embedder,
            use_relative_path=False,
        )
        
        assert ids[0] == f"myprefix:{file1.as_posix()}"

    def test_process_with_prefix_relative(self, tmp_path):
        """Test processing with ID prefix and relative path."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("Test content")
        
        mock_embedder = MagicMock()
        mock_embedder.addDocument.return_value = [0.1] * 768
        
        embeddings, documents, ids, updated_at_list, file_types = process_files(
            [file1],
            tmp_path,
            "myprefix",
            "note",
            mock_embedder,
            use_relative_path=True,
        )
        
        assert ids[0] == "myprefix:file1.txt"

    def test_skip_binary_files(self, tmp_path):
        """Test skipping binary files during processing."""
        text_file = tmp_path / "text.txt"
        binary_file = tmp_path / "binary.bin"
        text_file.write_text("Text content")
        binary_file.write_bytes(b"\x00\x01\x02")
        
        mock_embedder = MagicMock()
        mock_embedder.addDocument.return_value = [0.1] * 768
        
        embeddings, documents, ids, updated_at_list, file_types = process_files(
            [text_file, binary_file],
            tmp_path,
            "",
            "test",
            mock_embedder,
        )
        
        # Only text file should be processed
        assert len(embeddings) == 1


class TestCLIIntegration:
    """Integration tests for CLI."""

    @patch("semche.cli.bulk_register.Embedder")
    @patch("semche.cli.bulk_register.ChromaDBManager")
    def test_main_basic_flow(self, mock_chroma_cls, mock_embedder_cls, tmp_path):
        """Test basic CLI flow."""
        # Setup test files
        file1 = tmp_path / "test1.txt"
        file1.write_text("Content 1")
        
        # Mock embedder
        mock_embedder = MagicMock()
        mock_embedder.addDocument.return_value = [0.1] * 768
        mock_embedder_cls.return_value = mock_embedder
        
        # Mock ChromaDB manager
        mock_chroma = MagicMock()
        mock_chroma.persist_directory = str(tmp_path / "chroma")
        mock_chroma.save.return_value = {
            "status": "success",
            "count": 1,
            "collection": "documents",
            "persist_directory": str(tmp_path / "chroma"),
        }
        mock_chroma_cls.return_value = mock_chroma
        
        # Import main and run
        from semche.cli.bulk_register import main
        
        with patch("sys.argv", ["doc-update", str(file1), "--file-type", "test"]):
            result = main()
        
        assert result == 0
        assert mock_chroma.save.called

    @patch("semche.cli.bulk_register.Embedder")
    @patch("semche.cli.bulk_register.ChromaDBManager")
    def test_main_no_files_found(self, mock_chroma_cls, mock_embedder_cls, tmp_path):
        """Test CLI when no files are found."""
        from semche.cli.bulk_register import main
        
        nonexistent = tmp_path / "nonexistent"
        
        with patch("sys.argv", ["doc-update", str(nonexistent)]):
            result = main()
        
        assert result == 1  # Should fail


class TestCLIEndToEnd:
    """End-to-end tests using actual CLI (requires environment setup)."""

    def test_help_message(self):
        """Test CLI help message."""
        from semche.cli.bulk_register import parse_args
        
        with patch("sys.argv", ["doc-update", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                parse_args()
            assert exc_info.value.code == 0
