import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


# Mock ebooklib
try:
    from ebooklib import epub
except ImportError:
    epub = Mock()

# Mock BeautifulSoup
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = Mock()

from epub_mcp.tools.epub_helper import (
    EpubProcessingError,
    clean_html,
    convert_html_to_markdown,
    extract_chapter_html,
    extract_chapter_plain_text,
    extract_multiple_chapters,
    flatten_toc,
    get_all_epub_files,
    get_meta,
    get_toc,
    read_epub,
)


class TestEpubHelper:
    """Test EPUB helper functions"""

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

    @patch("epub_mcp.tools.epub_helper.epub.read_epub")
    def test_get_toc_success(self, mock_read_epub):
        """Test get_toc successful case"""
        # Mock EPUB book with TOC
        mock_book = Mock()
        mock_chapter1 = Mock()
        mock_chapter1.title = "Chapter 1"
        mock_chapter1.href = "chapter1.xhtml"
        mock_chapter2 = Mock()
        mock_chapter2.title = "Chapter 2"
        mock_chapter2.href = "chapter2.xhtml"

        mock_book.toc = [mock_chapter1, mock_chapter2]
        mock_read_epub.return_value = mock_book

        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            f.write(b"mock epub content")
            epub_path = f.name

        try:
            result = get_toc(epub_path)
            expected = [("Chapter 1", "chapter1.xhtml"), ("Chapter 2", "chapter2.xhtml")]
            assert result == expected
        finally:
            Path(epub_path).unlink(missing_ok=True)

    @patch("epub_mcp.tools.epub_helper.epub.read_epub")
    def test_get_toc_nested_structure(self, mock_read_epub):
        """Test get_toc with nested TOC structure"""
        # Mock EPUB book with nested TOC
        mock_book = Mock()
        mock_chapter1 = Mock()
        mock_chapter1.title = "Chapter 1"
        mock_chapter1.href = "chapter1.xhtml"
        mock_subchapter1 = Mock()
        mock_subchapter1.title = "Subchapter 1.1"
        mock_subchapter1.href = "subchapter1.1.xhtml"

        mock_book.toc = [(mock_chapter1, [mock_subchapter1])]
        mock_read_epub.return_value = mock_book

        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            f.write(b"mock epub content")
            epub_path = f.name

        try:
            result = get_toc(epub_path)
            expected = [("Chapter 1", "chapter1.xhtml"), ("Subchapter 1.1", "subchapter1.1.xhtml")]
            assert result == expected
        finally:
            Path(epub_path).unlink(missing_ok=True)

    def test_get_toc_file_not_found(self):
        """Test get_toc with non-existent file"""
        with pytest.raises(FileNotFoundError):
            get_toc("/path/to/nonexistent.epub")

    @patch("epub_mcp.tools.epub_helper.epub.read_epub")
    def test_get_toc_parsing_error(self, mock_read_epub):
        """Test get_toc with parsing error"""
        mock_read_epub.side_effect = Exception("EPUB parsing error")

        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            f.write(b"mock epub content")
            epub_path = f.name

        try:
            with pytest.raises(Exception):
                get_toc(epub_path)
        finally:
            Path(epub_path).unlink(missing_ok=True)

    @patch("epub_mcp.tools.epub_helper.epub.read_epub")
    def test_get_meta_success(self, mock_read_epub):
        """Test get_meta successful case"""
        # Mock EPUB book with metadata
        mock_book = Mock()

        # 设置 get_metadata 方法返回正确的格式
        def mock_get_metadata(_namespace, field):

            metadata_map = {
                "title": [("Test Book", {})],
                "creator": [("Test Author", {})],
                "language": [("en", {})],
                "identifier": [("test-id", {})],
                "date": [("2023-01-01", {})],
                "publisher": [("Test Publisher", {})],
                "description": [("Test description", {})],
            }
            return metadata_map.get(field, [])

        mock_book.get_metadata = mock_get_metadata
        mock_read_epub.return_value = mock_book

        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            f.write(b"mock epub content")
            epub_path = f.name

        try:
            result = get_meta(epub_path)
            expected = {
                "title": "Test Book",
                "creator": ["Test Author"],
                "language": "en",
                "identifier": "test-id",
                "date": "2023-01-01",
                "publisher": "Test Publisher",
                "description": "Test description",
            }
            assert result == expected
        finally:
            Path(epub_path).unlink(missing_ok=True)

    def test_get_meta_file_not_found(self):
        """Test get_meta with non-existent file"""
        with pytest.raises(FileNotFoundError):
            get_meta("/path/to/nonexistent.epub")

    @patch("epub_mcp.tools.epub_helper.epub.read_epub")
    def test_get_meta_parsing_error(self, mock_read_epub):
        """Test get_meta with parsing error"""
        mock_read_epub.side_effect = Exception("EPUB parsing error")

        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            f.write(b"mock epub content")
            epub_path = f.name

        try:
            with pytest.raises(Exception):
                get_meta(epub_path)
        finally:
            Path(epub_path).unlink(missing_ok=True)

    @patch("epub_mcp.tools.epub_helper.epub.read_epub")
    def test_read_epub_success(self, mock_read_epub):
        """Test read_epub successful case"""
        mock_book = Mock()
        mock_read_epub.return_value = mock_book

        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            f.write(b"mock epub content")
            epub_path = f.name

        try:
            result = read_epub(epub_path)
            assert result == mock_book
            mock_read_epub.assert_called_once_with(epub_path)
        finally:
            Path(epub_path).unlink(missing_ok=True)

    def test_flatten_toc_simple(self):
        """Test flatten_toc with simple TOC structure"""
        mock_chapter1 = Mock()
        mock_chapter1.title = "Chapter 1"
        mock_chapter1.href = "chapter1.xhtml"
        mock_chapter2 = Mock()
        mock_chapter2.title = "Chapter 2"
        mock_chapter2.href = "chapter2.xhtml"

        toc = [mock_chapter1, mock_chapter2]
        mock_book = Mock()
        mock_book.toc = toc
        result = flatten_toc(mock_book)

        expected = ["chapter1.xhtml", "chapter2.xhtml"]
        assert result == expected

    def test_flatten_toc_nested(self):
        """Test flatten_toc with nested TOC structure"""
        mock_chapter1 = Mock()
        mock_chapter1.title = "Chapter 1"
        mock_chapter1.href = "chapter1.xhtml"
        mock_subchapter1 = Mock()
        mock_subchapter1.title = "Subchapter 1.1"
        mock_subchapter1.href = "subchapter1.1.xhtml"

        toc = [(mock_chapter1, [mock_subchapter1])]
        mock_book = Mock()
        mock_book.toc = toc
        result = flatten_toc(mock_book)

        expected = ["chapter1.xhtml", "subchapter1.1.xhtml"]
        assert result == expected

    def test_clean_html(self):
        """Test clean_html function"""
        html_content = """
        <html>
            <head><title>Test</title></head>
            <body>
                <h1>Title</h1>
                <p>Content</p>
                <!-- Comment -->
                <script>alert('test');</script>
            </body>
        </html>
        """

        result = clean_html(html_content)

        # Should remove comments and scripts
        assert "<!-- Comment -->" not in result
        assert "<script>" not in result
        assert "alert('test');" not in result
        # Should keep content
        assert "<h1>Title</h1>" in result
        assert "<p>Content</p>" in result

    def test_convert_html_to_markdown(self):
        """Test convert_html_to_markdown function"""
        html_content = "<h1>Title</h1><p>This is <strong>bold</strong> text.</p>"

        result = convert_html_to_markdown(html_content)

        # Should convert HTML to markdown
        assert "# Title" in result
        assert "**bold**" in result

    @patch("epub_mcp.tools.epub_helper.extract_chapter_html")
    def test_extract_chapter_plain_text(self, mock_extract_html):
        """Test extract_chapter_plain_text function"""
        mock_extract_html.return_value = "<h1>Title</h1><p>Content</p>"

        mock_book = Mock()
        result = extract_chapter_plain_text(mock_book, "chapter1")

        mock_extract_html.assert_called_once_with(mock_book, "chapter1")
        # Should return plain text (HTML tags removed)
        assert "<h1>" not in result
        assert "<p>" not in result
        assert "Title" in result
        assert "Content" in result

    def test_extract_chapter_html_by_title_and_index(self):
        """Test extract_chapter_html with title matching and numeric index matching."""
        mock_item = Mock()
        mock_item.get_content.return_value = (
            b'<html><body><h1 id="sec2">Chapter Title</h1><p>Test text</p></body></html>'
        )

        mock_ch1 = Mock()
        mock_ch1.title = "CHAPTER II. The Pool of Tears"
        mock_ch1.href = "ch02.html#sec2"

        mock_book = Mock()
        mock_book.toc = [mock_ch1]
        mock_book.get_item_with_href.return_value = mock_item

        # 1. Match by exact title
        html_by_title = extract_chapter_html(mock_book, "CHAPTER II. The Pool of Tears")
        assert "Chapter Title" in html_by_title

        # 2. Match by case-insensitive title
        html_by_lower = extract_chapter_html(mock_book, "chapter ii. the pool of tears")
        assert "Chapter Title" in html_by_lower

        # 3. Match by 1-based index
        html_by_index = extract_chapter_html(mock_book, "1")
        assert "Chapter Title" in html_by_index

    def test_extract_chapter_html_container_div(self):
        """Test extract_chapter_html when anchor element is a div container."""

        mock_item = Mock()
        mock_item.get_content.return_value = (
            b'<html xmlns="http://www.w3.org/1999/xhtml">'
            b'<body><div class="chapter" id="pgepubid00003">'
            b"<h2>CHAPTER I. Down the Rabbit-Hole</h2>"
            b"<p>Alice was beginning to get very tired of sitting by her sister.</p>"
            b"</div></body></html>"
        )

        mock_ch1 = Mock()
        mock_ch1.title = "CHAPTER I. Down the Rabbit-Hole"
        mock_ch1.href = "ch01.html#pgepubid00003"

        mock_book = Mock()
        mock_book.toc = [mock_ch1]
        mock_book.get_item_with_href.return_value = mock_item

        html = extract_chapter_html(mock_book, "ch01.html#pgepubid00003")
        assert "CHAPTER I. Down the Rabbit-Hole" in html
        assert "Alice was beginning to get very tired" in html

    def test_epub_processing_error_attributes(self):
        """Test EpubProcessingError attributes initialization"""
        orig_err = ValueError("Original root cause")
        err = EpubProcessingError(
            "Test error message",
            file_path="/path/to/book.epub",
            operation="test_op",
            original_error=orig_err,
        )
        assert err.message == "Test error message"
        assert err.file_path == "/path/to/book.epub"
        assert err.operation == "test_op"
        assert err.original_error == orig_err
        assert "(file: /path/to/book.epub, operation: test_op)" in str(err)

    def test_extract_chapter_from_epub(self):
        """Test extract_chapter_from_epub wrapper function"""
        mock_ch = Mock()
        mock_ch.title = "Chapter 1"
        mock_ch.href = "ch01.html"

        mock_item = Mock()
        mock_item.get_content.return_value = (
            b"<html><body><h2>Chapter 1</h2><p>Content</p></body></html>"
        )

        mock_book = Mock()
        mock_book.toc = [mock_ch]
        mock_book.get_item_with_href.return_value = mock_item

        with patch("epub_mcp.tools.epub_helper.epub.read_epub", return_value=mock_book):
            from epub_mcp.tools.epub_helper import extract_chapter_from_epub

            html = extract_chapter_from_epub("/fake/book.epub", "Chapter 1")
            assert "Chapter 1" in html

    def test_extract_chapter_html_errors(self):
        """Test extract_chapter_html error conditions"""
        mock_ch = Mock()
        mock_ch.title = "Chapter I"
        mock_ch.href = "ch01.html#sec1"

        mock_book = Mock()
        mock_book.toc = [mock_ch]

        # 1. Chapter not found in TOC
        with pytest.raises(EpubProcessingError, match="not found in TOC"):
            extract_chapter_html(mock_book, "Nonexistent Chapter")

        # 2. Chapter file not found in book
        mock_book.get_item_with_href.return_value = None
        with pytest.raises(EpubProcessingError, match="Chapter file not found"):
            extract_chapter_html(mock_book, "Chapter I")

        # 3. Anchor not found in chapter HTML
        mock_item = Mock()
        mock_item.get_content.return_value = b"<html><body><p>No anchor</p></body></html>"
        mock_book.get_item_with_href.return_value = mock_item
        with pytest.raises(EpubProcessingError, match="Anchor sec1 not found"):
            extract_chapter_html(mock_book, "Chapter I")

    def test_extract_chapter_html_partial_title_and_body_fallback(self):
        """Test partial title matching and body element fallback"""
        mock_item = Mock()
        mock_item.get_content.return_value = (
            b"<html><body><p>Plain text content without headings</p></body></html>"
        )

        mock_ch = Mock()
        mock_ch.title = "CHAPTER II. The Pool of Tears"
        mock_ch.href = "ch02.html"

        mock_book = Mock()
        mock_book.toc = [mock_ch]
        mock_book.get_item_with_href.return_value = mock_item

        # Partial title match ('Pool of Tears')
        html = extract_chapter_html(mock_book, "Pool of Tears")
        assert "Plain text content without headings" in html

    def test_extract_multiple_chapters(self):
        """Test extract_multiple_chapters function with various output formats"""
        mock_item = Mock()
        mock_item.get_content.return_value = (
            b"<html><body><h2>Chapter 1</h2><p>Content</p></body></html>"
        )

        mock_ch = Mock()
        mock_ch.title = "Chapter 1"
        mock_ch.href = "ch01.html"

        mock_book = Mock()
        mock_book.toc = [mock_ch]
        mock_book.get_item_with_href.return_value = mock_item

        # 1. HTML output
        res_html = extract_multiple_chapters(mock_book, ["Chapter 1"], output="html")
        assert res_html[0][0] == "Chapter 1"
        assert "Chapter 1" in res_html[0][1]

        # 2. Text output
        res_text = extract_multiple_chapters(mock_book, ["Chapter 1"], output="text")
        assert "Chapter 1" in res_text[0][1]

        # 3. Markdown output
        res_md = extract_multiple_chapters(mock_book, ["Chapter 1"], output="markdown")
        assert "Chapter 1" in res_md[0][1]

        # 4. Invalid output format
        with pytest.raises(ValueError, match="Invalid output format"):
            extract_multiple_chapters(mock_book, ["Chapter 1"], output="invalid")
