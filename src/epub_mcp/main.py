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


@mcp.tool()
@handle_mcp_errors
def get_epub_chapter_markdown(
    epub_path: str, chapter_id: str, start_index: int = 0, page_size: int = 50000
) -> str:
    """Get content of an EPUB chapter in markdown format with optional pagination.

    Args:
        epub_path: Path to the EPUB file.
        chapter_id: Chapter identifier. Accepts chapter title (e.g. 'CHAPTER II'),
            href link from get_epub_toc, or 1-based chapter index (e.g. '5').
        start_index: Starting character index for pagination (default: 0).
        page_size: Maximum number of characters to return (default: 50000).

    Returns:
        str: Chapter content in markdown format (paginated if truncated).
    """
    clean_path = str(
        security.validate_file_path(epub_path, allowed_extensions={".epub"}, must_exist=False)
    )
    logger.debug(
        f"calling get_epub_chapter_markdown: {clean_path}, chapter ID: {chapter_id}, "
        f"start: {start_index}, size: {page_size}"
    )
    book = epub_helper.read_epub(clean_path)
    full_content = epub_helper.extract_chapter_markdown(book, chapter_id)

    end_index = start_index + page_size
    paginated_content = full_content[start_index:end_index]

    if end_index < len(full_content):
        paginated_content += (
            f"\n\n[Content truncated. Total length: {len(full_content)} characters. "
            f"Use start_index={end_index} to continue.]"
        )

    return paginated_content


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
