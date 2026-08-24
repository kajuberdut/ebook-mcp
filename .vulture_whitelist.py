# Vulture whitelist for FastMCP tools, prompts, framework attributes, and test mocks
from unittest.mock import Mock  # noqa: F401

import html2text  # noqa: F401
import main  # noqa: F401
import main as mcp  # noqa: F401

from ebook_mcp.tests import conftest  # noqa: F401
from ebook_mcp.tools import epub_helper  # noqa: F401

# FastMCP Prompts and Tools (invoked dynamically by FastMCP framework)
main.summarize_chapter
main.generate_quiz
main.get_all_epub_files
main.get_epub_metadata
main.get_epub_toc
main.get_epub_chapter_markdown
mcp.settings.transport_security

# EPUB Helper API functions & html2text attributes
epub_helper.extract_chapter_from_epub
epub_helper.extract_multiple_chapters

# html2text attributes
h = html2text.HTML2Text()
h.ignore_links
h.ignore_images

# Unittest mock attributes
mock = Mock()
mock.return_value
mock.side_effect

# Pytest fixtures in conftest.py
conftest.mock_epub_book
conftest.sample_epub_files
conftest.temp_epub_file
