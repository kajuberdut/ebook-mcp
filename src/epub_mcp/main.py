import logging
import os
import warnings
from collections.abc import Callable
from functools import wraps

# Suppress upstream pydantic_settings forward reference warnings at module load time
warnings.filterwarnings("ignore", message=".*Field 'lifespan' has an incomplete definition.*")

from mcp.server.fastmcp import FastMCP  # noqa: E402
from mcp.server.transport_security import TransportSecuritySettings  # noqa: E402

from epub_mcp.tools import epub_helper, security  # noqa: E402
from epub_mcp.tools.logger_config import setup_logger  # noqa: E402


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
        except epub_helper.EpubProcessingError as e:
            raise e
        except Exception as e:
            raise Exception(str(e))

    return wrapper


logger = logging.getLogger(__name__)


# Initialize FastMCP server with instructions
mcp = FastMCP(
    "epub-mcp",
    instructions=(
        "Epub-MCP is a Model Context Protocol server for processing EPUB e-books. "
        "It provides standardized tools to extract metadata, table of contents, "
        "and chapter content. Always supply absolute file paths."
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
    """Get table of contents of an EPUB file as a list of (title, href) tuples.

    Either the chapter title (e.g. 'CHAPTER II. The Pool of Tears'), href link, or 1-based index
    can be passed as chapter_id to get_epub_chapter_markdown.
    """
    clean_path = str(
        security.validate_file_path(epub_path, allowed_extensions={".epub"}, must_exist=False)
    )
    logger.debug(f"calling get_epub_toc: {clean_path}")
    return epub_helper.get_toc(clean_path)


MAX_PAGE_SIZE = 200000


@mcp.tool()
@handle_mcp_errors
def get_epub_chapter_markdown(
    epub_path: str, chapter_id: str, start_index: int = 0, page_size: int = 50000
) -> dict[str, str | int | bool | None]:
    """Get content of an EPUB chapter in markdown format with structured pagination metadata.

    Args:
        epub_path: Path to the EPUB file.
        chapter_id: Chapter identifier. Accepts chapter title (e.g. 'CHAPTER II'),
            href link from get_epub_toc, or 1-based chapter index (e.g. '5').
        start_index: Starting character index for pagination (0-based, default: 0).
            Must be >= 0.
        page_size: Maximum characters to return per page (default: 50000, max: 200000).
            Must be >= 1.

    Returns:
        Dict containing:
            - content (str): Paginated chapter markdown text.
            - start_index (int): Starting character index of this chunk.
            - end_index (int): Ending character index of this chunk.
            - total_length (int): Total character length of full chapter.
            - has_more (bool): Whether additional content remains after this chunk.
            - next_start_index (int | None): start_index to pass in next call (None if done).
            - total_pages (int): Calculated total pages ((total_length + page_size - 1) // size).


    Examples:
        Initial fetch (Page 1 of chapter):
        >>> get_epub_chapter_markdown("/library/alice.epub", "Chapter 1", page_size=50000)
        {
            "content": "# CHAPTER I. Down the Rabbit-Hole...",
            "start_index": 0,
            "end_index": 49850,
            "total_length": 120000,
            "has_more": True,
            "next_start_index": 49850,
            "total_pages": 3
        }

        Fetching next chunk using returned next_start_index:
        >>> get_epub_chapter_markdown(
        ...     "/library/alice.epub", "Chapter 1", start_index=49850, page_size=50000
        ... )

        Reaching end of chapter:
        >>> get_epub_chapter_markdown(
        ...     "/library/alice.epub", "Chapter 1", start_index=150000, page_size=50000
        ... )
        {
            "content": "",
            "start_index": 150000,
            "end_index": 120000,
            "total_length": 120000,
            "has_more": False,
            "next_start_index": None,
            "total_pages": 3,
            "message": "No more content available. Total length: 120000 characters."
        }
    """
    if start_index < 0:
        raise ValueError(f"start_index must be >= 0 (got {start_index})")
    if page_size <= 0 or page_size > MAX_PAGE_SIZE:
        raise ValueError(f"page_size must be between 1 and {MAX_PAGE_SIZE} (got {page_size})")

    clean_path = str(
        security.validate_file_path(epub_path, allowed_extensions={".epub"}, must_exist=False)
    )
    book = epub_helper.read_epub(clean_path)
    full_content = epub_helper.extract_chapter_markdown(book, chapter_id)
    total_length = len(full_content)

    logger.debug(
        f"calling get_epub_chapter_markdown: {clean_path}, chapter ID: {chapter_id}, "
        f"start_index: {start_index}, page_size: {page_size}, total_length: {total_length}"
    )

    total_pages = (total_length + page_size - 1) // page_size if total_length > 0 else 0

    if start_index >= total_length:
        return {
            "content": "",
            "start_index": start_index,
            "end_index": total_length,
            "total_length": total_length,
            "has_more": False,
            "next_start_index": None,
            "total_pages": total_pages,
            "message": f"No more content available. Total length: {total_length} characters.",
        }

    raw_end_index = min(start_index + page_size, total_length)
    actual_end_index = raw_end_index

    # Semantic boundary optimization: slice at nearest newline break to avoid cutting mid-line

    if raw_end_index < total_length:
        lookback = max(start_index + 100, raw_end_index - 500)
        newline_pos = full_content.rfind("\n", lookback, raw_end_index)
        if newline_pos != -1:
            actual_end_index = newline_pos + 1

    paginated_content = full_content[start_index:actual_end_index]
    has_more = actual_end_index < total_length
    next_start_index = actual_end_index if has_more else None

    return {
        "content": paginated_content,
        "start_index": start_index,
        "end_index": actual_end_index,
        "total_length": total_length,
        "has_more": has_more,
        "next_start_index": next_start_index,
        "total_pages": total_pages,
    }


# Entry point for the package CLI (epub-mcp)


def cli_entry():
    setup_logger()
    transport = os.getenv("EPUB_MCP_TRANSPORT", os.getenv("EBOOK_MCP_TRANSPORT", "stdio")).lower()
    host = os.getenv("EPUB_MCP_HOST", os.getenv("EBOOK_MCP_HOST", "0.0.0.0"))
    port = int(os.getenv("EPUB_MCP_PORT", os.getenv("EBOOK_MCP_PORT", "8000")))

    logger.info(f"Starting epub-mcp server (transport={transport})")
    mcp.settings.host = host
    mcp.settings.port = port

    # Configure DNS rebinding / host header security validation rules for network transport
    raw_hosts = os.getenv("EPUB_MCP_ALLOWED_HOSTS", os.getenv("EBOOK_MCP_ALLOWED_HOSTS", "*"))
    raw_origins = os.getenv("EPUB_MCP_ALLOWED_ORIGINS", os.getenv("EBOOK_MCP_ALLOWED_ORIGINS", "*"))

    if raw_hosts == "*" or raw_origins == "*":
        logger.warning(
            "UNSAFE DEFAULTS WARNING: FastMCP is using wildcard allowed hosts/origins ('*') "
            "with DNS rebinding protection disabled. Suitable for dev/testing, NOT production. "
            "To resolve for production, set EPUB_MCP_ALLOWED_HOSTS and EPUB_MCP_ALLOWED_ORIGINS "
            "to specific host lists (e.g. 'myhost.com,192.168.1.100')."
        )
        mcp.settings.transport_security = TransportSecuritySettings(
            enable_dns_rebinding_protection=False,
            allowed_hosts=[
                "localhost:*",
                "127.0.0.1:*",
                "[::1]:*",
                "epub-mcp-server:*",
                "ebook-mcp-server:*",
                "0.0.0.0:*",
                "*",
                "*:*",
            ],
            allowed_origins=[
                "http://localhost:*",
                "http://127.0.0.1:*",
                "http://[::1]:*",
                "http://epub-mcp-server:*",
                "http://ebook-mcp-server:*",
                "http://0.0.0.0:*",
                "*",
                "*:*",
            ],
        )
    else:
        allowed_hosts = [h.strip() for h in raw_hosts.split(",")]
        allowed_origins = [o.strip() for o in raw_origins.split(",")]
        mcp.settings.transport_security = TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=allowed_hosts,
            allowed_origins=allowed_origins,
        )

    allowed_dir_env = os.getenv("EPUB_MCP_ALLOWED_DIR", os.getenv("EBOOK_MCP_ALLOWED_DIR"))
    if not allowed_dir_env:
        logger.warning(
            "UNSAFE DEFAULTS WARNING: EPUB_MCP_ALLOWED_DIR environment variable is not set. "
            "File path boundaries are unconstrained. To resolve for production, set "
            "EPUB_MCP_ALLOWED_DIR to your book directory path (e.g. '/library')."
        )

    if transport == "sse":
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    cli_entry()
