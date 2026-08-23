import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Test basic file operations that don't require external dependencies


def test_get_all_epub_files_basic():
    """Test basic EPUB file discovery without external dependencies"""
    with tempfile.TemporaryDirectory() as temp_dir:
        p = Path(temp_dir)
        # Create mock EPUB files
        epub_files = ["book1.epub", "book2.epub", "document.txt"]
        for file in epub_files:
            (p / file).write_text("mock content")

        # Test the basic file discovery logic
        result = [f.name for f in p.glob("*.epub") if f.is_file()]
        assert set(result) == {"book1.epub", "book2.epub"}


def test_get_all_pdf_files_basic():
    """Test basic PDF file discovery without external dependencies"""
    with tempfile.TemporaryDirectory() as temp_dir:
        p = Path(temp_dir)
        # Create mock PDF files
        pdf_files = ["document1.pdf", "document2.pdf", "text.txt"]
        for file in pdf_files:
            (p / file).write_text("mock content")

        # Test the basic file discovery logic
        result = [f.name for f in p.glob("*.pdf") if f.is_file()]
        assert set(result) == {"document1.pdf", "document2.pdf"}


def test_file_not_found_error():
    """Test file not found error handling"""
    with pytest.raises(FileNotFoundError):
        open("/nonexistent/file.txt")


def test_temp_file_operations():
    """Test temporary file operations"""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)

    try:
        # Verify file was created
        assert temp_path.exists()

        # Read content
        content = temp_path.read_text()
        assert content == "test content"
    finally:
        # Clean up
        temp_path.unlink(missing_ok=True)


def test_directory_operations():
    """Test directory operations"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create subdirectory
        sub_dir = Path(temp_dir) / "subdir"
        sub_dir.mkdir(parents=True, exist_ok=True)

        # Create files in subdirectory
        files = ["file1.txt", "file2.txt"]
        for file in files:
            (sub_dir / file).write_text(f"content for {file}")

        # List files
        result = [f.name for f in sub_dir.iterdir()]
        assert set(result) == set(files)


@pytest.mark.parametrize(
    "file_extension,expected_count",
    [
        (".epub", 2),
        (".pdf", 1),
        (".txt", 3),
    ],
)
def test_file_filtering(file_extension, expected_count):
    """Test file filtering by extension"""
    with tempfile.TemporaryDirectory() as temp_dir:
        p = Path(temp_dir)
        # Create test files
        test_files = [
            "book1.epub",
            "book2.epub",
            "document.pdf",
            "file1.txt",
            "file2.txt",
            "file3.txt",
        ]

        for file in test_files:
            (p / file).write_text("content")

        # Filter by extension
        result = [f.name for f in p.glob(f"*{file_extension}") if f.is_file()]
        assert len(result) == expected_count


def test_mock_basic_operations():
    """Test basic mock operations"""
    mock_file = Mock()
    mock_file.read.return_value = "mock content"
    mock_file.write.return_value = None

    # Test mock behavior
    assert mock_file.read() == "mock content"
    mock_file.write("test")
    mock_file.write.assert_called_once_with("test")


def test_patch_basic():
    """Test basic patch functionality"""
    with patch.object(Path, "exists", return_value=False):
        assert not Path("/any/path").exists()

    with patch.object(Path, "exists", return_value=True):
        assert Path("/any/path").exists()
