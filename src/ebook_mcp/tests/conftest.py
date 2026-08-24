import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def mock_epub_book():
    """Create a mock EPUB book for testing"""
    mock_book = Mock()
    mock_book.get_metadata.return_value = {
        "title": [("Test Book", {})],
        "creator": [("Test Author", {})],
        "language": [("en", {})],
        "identifier": [("test-id", {})],
        "date": [("2023-01-01", {})],
        "publisher": [("Test Publisher", {})],
        "description": [("Test description", {})],
    }
    return mock_book


@pytest.fixture
def sample_epub_files():
    """Create sample EPUB file names for testing"""
    return ["book1.epub", "book2.epub", "document.txt"]


@pytest.fixture
def temp_epub_file():
    """Create a temporary EPUB file for testing"""
    with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
        f.write(b"mock epub content")
        epub_path = f.name

    yield epub_path

    # Cleanup
    Path(epub_path).unlink(missing_ok=True)
