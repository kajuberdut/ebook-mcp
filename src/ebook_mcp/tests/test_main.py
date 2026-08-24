import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


# Mock mcp.server.fastmcp
try:
    import mcp.server.fastmcp
except ImportError:
    sys.modules["mcp.server.fastmcp"] = Mock()
    sys.modules["mcp"] = Mock()
    sys.modules["mcp.server"] = Mock()

# Import the functions to test
from ebook_mcp.main import (
    get_all_epub_files,
    get_epub_metadata,
    get_epub_toc,
)


class TestEpubFunctions:
    """Test EPUB related functions"""

    def test_get_all_epub_files_empty_directory(self):
        """Test get_all_epub_files with empty directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = get_all_epub_files(temp_dir)
            assert result == []

    def test_get_all_epub_files_with_epub_files(self):
        """Test get_all_epub_files with EPUB files present"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock EPUB files
            epub_files = ["book1.epub", "book2.epub", "document.txt"]
            for file in epub_files:
                with open(Path(temp_dir) / file, "w") as f:
                    f.write("mock content")

            result = get_all_epub_files(temp_dir)
            assert set(result) == {"book1.epub", "book2.epub"}

    @patch("ebook_mcp.main.epub_helper.get_meta")
    def test_get_epub_metadata_success(self, mock_get_meta):
        """Test get_epub_metadata successful case"""
        mock_metadata = {"title": "Test Book", "author": "Test Author", "language": "en"}
        mock_get_meta.return_value = mock_metadata

        result = get_epub_metadata("/path/to/test.epub")
        assert result == mock_metadata
        mock_get_meta.assert_called_once_with("/path/to/test.epub")

    @patch("ebook_mcp.main.epub_helper.get_meta")
    def test_get_epub_metadata_file_not_found(self, mock_get_meta):
        """Test get_epub_metadata with file not found"""
        mock_get_meta.side_effect = FileNotFoundError("File not found")

        with pytest.raises(FileNotFoundError):
            get_epub_metadata("/path/to/nonexistent.epub")

    @patch("ebook_mcp.main.epub_helper.get_meta")
    def test_get_epub_metadata_parsing_error(self, mock_get_meta):
        """Test get_epub_metadata with parsing error"""
        mock_get_meta.side_effect = Exception("Parsing error")

        with pytest.raises(Exception):
            get_epub_metadata("/path/to/corrupted.epub")

    @patch("ebook_mcp.main.epub_helper.get_toc")
    def test_get_epub_toc_success(self, mock_get_toc):
        """Test get_epub_toc successful case"""
        mock_toc = [("Chapter 1", "chapter1.xhtml"), ("Chapter 2", "chapter2.xhtml")]
        mock_get_toc.return_value = mock_toc

        result = get_epub_toc("/path/to/test.epub")
        assert result == mock_toc
        mock_get_toc.assert_called_once_with("/path/to/test.epub")

    @patch("ebook_mcp.main.epub_helper.get_toc")
    def test_get_epub_toc_file_not_found(self, mock_get_toc):
        """Test get_epub_toc with file not found"""
        mock_get_toc.side_effect = FileNotFoundError("File not found")

        with pytest.raises(FileNotFoundError):
            get_epub_toc("/path/to/nonexistent.epub")


class TestMainModule:
    """Test main module functionality"""

    def test_main_module_imports(self):
        """Test that main module can be imported without errors"""
        import ebook_mcp.main

        assert hasattr(ebook_mcp.main, "mcp")
        assert hasattr(ebook_mcp.main, "get_all_epub_files")

    @patch("ebook_mcp.main.mcp.run")
    def test_cli_entry_function(self, mock_mcp_run):
        """Test cli_entry function launches the registered FastMCP server"""
        from ebook_mcp.main import cli_entry

        cli_entry()
        mock_mcp_run.assert_called_once_with(transport="stdio")


class TestDecorators:
    """Test the error handling decorators"""

    def test_handle_mcp_errors_file_not_found(self):
        """Test handle_mcp_errors decorator with FileNotFoundError"""
        from ebook_mcp.main import handle_mcp_errors

        @handle_mcp_errors
        def test_function():
            raise FileNotFoundError("Test file not found")

        with pytest.raises(FileNotFoundError, match="Test file not found"):
            test_function()

    def test_handle_mcp_errors_general_exception(self):
        """Test handle_mcp_errors decorator with general exception"""
        from ebook_mcp.main import handle_mcp_errors

        @handle_mcp_errors
        def test_function():
            raise ValueError("Test value error")

        with pytest.raises(Exception, match="Test value error"):
            test_function()

    def test_decorator_preserves_return_value(self):
        """Test that decorators preserve return values"""
        from ebook_mcp.main import handle_mcp_errors

        @handle_mcp_errors
        def test_function():
            return "test result"

        result = test_function()
        assert result == "test result"

    def test_handle_mcp_errors_with_custom_exceptions(self):
        """Test handle_mcp_errors decorator with custom exceptions"""
        from ebook_mcp.main import handle_mcp_errors
        from ebook_mcp.tools.epub_helper import EpubProcessingError

        @handle_mcp_errors
        def test_epub_function():
            raise EpubProcessingError("Test EPUB error", "/test.epub", "test_operation")

        # Custom exceptions should be re-raised as-is
        with pytest.raises(EpubProcessingError, match="Test EPUB error"):
            test_epub_function()
