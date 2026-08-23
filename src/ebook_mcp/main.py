import logging
import os
from collections.abc import Callable
from functools import wraps

from mcp.server.fastmcp import FastMCP

from ebook_mcp.tools import epub_helper, pdf_helper, security
from ebook_mcp.tools.logger_config import setup_logger


def handle_mcp_errors[T](func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to handle common MCP tool errors uniformly."""

    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except (FileNotFoundError, security.SecurityValidationError, ValueError) as e:
            if isinstance(e, FileNotFoundError):
                raise FileNotFoundError(str(e))
            raise ValueError(str(e))
        except (epub_helper.EpubProcessingError, pdf_helper.PdfProcessingError) as e:
            raise e
        except Exception as e:
            raise Exception(str(e))

    return wrapper


def handle_pdf_errors[T](func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to handle PDF-specific errors."""

    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except (FileNotFoundError, security.SecurityValidationError, ValueError) as e:
            if isinstance(e, FileNotFoundError):
                raise FileNotFoundError(str(e))
            raise ValueError(str(e))
        except Exception as e:
            raise Exception(str(e))

    return wrapper


logger = logging.getLogger(__name__)


# Initialize FastMCP server with instructions
mcp = FastMCP(
    "ebook-mcp",
    instructions=(
        "Ebook-MCP is a Model Context Protocol server for processing EPUB and PDF e-books. "
        "It provides standardized tools to extract metadata, table of contents, and content. "
        "Use EPUB tools for .epub files and PDF tools for .pdf files. "
        "Always supply absolute file paths."
    ),
)


# FastMCP Prompts
@mcp.prompt()
def summarize_chapter(book_path: str, chapter_identifier: str) -> str:
    """Generate a prompt asking the AI model to summarize a specific chapter of an e-book."""
    return (
        f"Please analyze and summarize the content of chapter '{chapter_identifier}' "
        f"from the e-book at path '{book_path}'. "
        "Highlight key takeaways, core concepts, and main arguments."
    )


@mcp.prompt()
def generate_quiz(book_path: str, chapter_identifier: str, num_questions: int = 5) -> str:
    """Generate a prompt asking the AI model to create quiz questions from a chapter."""
    return (
        f"Based on the content of chapter '{chapter_identifier}' from path '{book_path}', "
        f"generate a {num_questions}-question study quiz with questions, "
        "answer key, and explanations."
    )



# EPUB related tools
@mcp.tool()
@handle_mcp_errors
def get_all_epub_files(path: str) -> list[str]:
    """Get all EPUB files in a given directory path."""
    clean_path = str(security.validate_file_path(path, must_exist=False))
    return epub_helper.get_all_epub_files(clean_path)


@mcp.tool()
@handle_mcp_errors
def get_epub_metadata(epub_path: str) -> dict[str, str | list[str]]:
    """Get metadata from an EPUB ebook file."""
    clean_path = str(
        security.validate_file_path(epub_path, allowed_extensions={".epub"}, must_exist=False)
    )
    logger.debug(f"Getting ebook metadata: {clean_path}")
    return epub_helper.get_meta(clean_path)


@mcp.tool()
@handle_mcp_errors
def get_epub_toc(epub_path: str) -> list[tuple[str, str]]:
    """Get table of contents of an EPUB file."""
    clean_path = str(
        security.validate_file_path(epub_path, allowed_extensions={".epub"}, must_exist=False)
    )
    logger.debug(f"calling get_epub_toc: {clean_path}")
    return epub_helper.get_toc(clean_path)


@mcp.tool()
@handle_mcp_errors
def get_epub_chapter_markdown(epub_path: str, chapter_id: str) -> str:
    """Get content of an EPUB chapter in markdown format by its chapter ID/href."""
    clean_path = str(
        security.validate_file_path(epub_path, allowed_extensions={".epub"}, must_exist=False)
    )
    logger.debug(f"calling get_epub_chapter_markdown: {clean_path}, chapter ID: {chapter_id}")
    book = epub_helper.read_epub(clean_path)
    return epub_helper.extract_chapter_markdown(book, chapter_id)


# PDF related tools
@mcp.tool()
@handle_mcp_errors
def get_all_pdf_files(path: str) -> list[str]:
    """Get all PDF files in a given directory path."""
    clean_path = str(security.validate_file_path(path, must_exist=False))
    return pdf_helper.get_all_pdf_files(clean_path)


@mcp.tool()
@handle_mcp_errors
def get_pdf_metadata(pdf_path: str) -> dict[str, str | list[str]]:
    """Get metadata of a PDF file."""
    clean_path = str(
        security.validate_file_path(pdf_path, allowed_extensions={".pdf"}, must_exist=False)
    )
    logger.debug(f"calling get_pdf_metadata: {clean_path}")
    return pdf_helper.get_meta(clean_path)


@mcp.tool()
@handle_mcp_errors
def get_pdf_toc(pdf_path: str) -> list[tuple[str, int]]:
    """Get table of contents of a PDF file."""
    clean_path = str(
        security.validate_file_path(pdf_path, allowed_extensions={".pdf"}, must_exist=False)
    )
    logger.debug(f"calling get_pdf_toc: {clean_path}")
    return pdf_helper.get_toc(clean_path)


@mcp.tool()
@handle_pdf_errors
def get_pdf_page_text(pdf_path: str, page_number: int) -> str:
    """Get plain text content of a specific page in a PDF file (1-based index)."""
    clean_path = str(
        security.validate_file_path(pdf_path, allowed_extensions={".pdf"}, must_exist=False)
    )
    clean_page = security.validate_page_number(page_number)
    logger.debug(f"calling get_pdf_page_text: {clean_path}, page: {clean_page}")
    return pdf_helper.extract_page_text(clean_path, clean_page)


@mcp.tool()
@handle_pdf_errors
def get_pdf_page_markdown(pdf_path: str, page_number: int) -> str:
    """Get markdown formatted content of a specific page in a PDF file (1-based index)."""
    clean_path = str(
        security.validate_file_path(pdf_path, allowed_extensions={".pdf"}, must_exist=False)
    )
    clean_page = security.validate_page_number(page_number)
    logger.debug(f"calling get_pdf_page_markdown: {clean_path}, page: {clean_page}")
    return pdf_helper.extract_page_markdown(clean_path, clean_page)


@mcp.tool()
@handle_pdf_errors
def get_pdf_chapter_content(pdf_path: str, chapter_title: str) -> tuple[str, list[int]]:
    """Get content of a specific chapter in a PDF file by its title."""
    clean_path = str(
        security.validate_file_path(pdf_path, allowed_extensions={".pdf"}, must_exist=False)
    )
    logger.debug(f"calling get_pdf_chapter_content: {clean_path}, chapter: {chapter_title}")
    return pdf_helper.extract_chapter_by_title(clean_path, chapter_title)


# Entry point for the package CLI (ebook-mcp)
def cli_entry():
    setup_logger()
    transport = os.getenv("EBOOK_MCP_TRANSPORT", "stdio").lower()
    host = os.getenv("EBOOK_MCP_HOST", "0.0.0.0")
    port = int(os.getenv("EBOOK_MCP_PORT", "8000"))

    logger.info(f"Starting ebook-mcp server (transport={transport})")
    if transport == "sse":
        mcp.run(transport="sse", host=host, port=port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    cli_entry()
