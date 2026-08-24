from pathlib import Path
from typing import Any

from .logger_config import get_logger, log_operation


# Custom exception classes for better error handling
class EpubProcessingError(Exception):
    """Custom exception for EPUB processing errors with detailed context"""

    def __init__(
        self, message: str, file_path: str, operation: str, original_error: Exception = None
    ):
        self.message = message
        self.file_path = file_path
        self.operation = operation
        self.original_error = original_error
        super().__init__(f"{message} (file: {file_path}, operation: {operation})")


try:
    from ebooklib import epub
except ImportError:
    epub = None

try:
    from bs4 import BeautifulSoup, Comment
except ImportError:
    BeautifulSoup = None
    Comment = None

try:
    import html2text
except ImportError:
    html2text = None

# Initialize structured logger
logger = get_logger(__name__)


def get_all_epub_files(path: str) -> list[str]:
    """
    Get all EPUB files in the specified path
    """
    p = Path(path)
    if not p.is_dir():
        return []
    return [f.name for f in p.glob("*.epub") if f.is_file()]


@log_operation("epub_toc_extraction")
def get_toc(epub_path: str) -> list[tuple[str, str]]:
    """
    Get the Table of Contents (TOC) from an EPUB file

    Args:
        epub_path (str): Absolute path to the EPUB file

    Returns:
        List[Tuple[str, str]]: List of TOC entries, each entry is a tuple of (title, link)

    Raises:
        FileNotFoundError: If the file does not exist
        Exception: If the file is not a valid EPUB or parsing fails
    """
    try:
        if not Path(epub_path).exists():
            logger.error("EPUB file not found", file_path=epub_path, operation="toc_extraction")
            raise FileNotFoundError(f"EPUB file not found: {epub_path}")

        # Read EPUB file
        logger.debug(
            "Starting EPUB TOC extraction", file_path=epub_path, operation="toc_extraction"
        )
        book = epub.read_epub(epub_path)
        toc = []

        # Iterate through TOC items
        for item in book.toc:
            # Handle nested TOC structure
            if isinstance(item, tuple):
                # item format: (chapter element, list of subchapters)
                chapter = item[0]
                toc.append((chapter.title, chapter.href))
                # Add subchapters
                for sub_item in item[1]:
                    if isinstance(sub_item, tuple):
                        toc.append((sub_item[0].title, sub_item[0].href))
                    else:
                        toc.append((sub_item.title, sub_item.href))
            else:
                # Single level TOC item
                toc.append((item.title, item.href))

        logger.info(
            "EPUB TOC extraction completed",
            file_path=epub_path,
            operation="toc_extraction",
            chapter_count=len(toc),
        )
        return toc
    except FileNotFoundError:
        raise FileNotFoundError(f"EPUB file not found: {epub_path}")
    except Exception as e:
        logger.error(
            "Failed to parse EPUB file",
            file_path=epub_path,
            operation="toc_extraction",
            error_type=type(e).__name__,
            error_details=str(e),
        )
        raise EpubProcessingError("Failed to parse EPUB file", epub_path, "toc_extraction", e)


@log_operation("epub_metadata_extraction")
def get_meta(epub_path: str) -> dict[str, str | list[str]]:
    """
    Get metadata from an EPUB file

    Args:
        epub_path (str): Absolute path to the EPUB file

    Returns:
        Dict[str, Union[str, List[str]]]: Dictionary containing metadata

    Raises:
        FileNotFoundError: If the file does not exist
        Exception: If the file is not a valid EPUB or parsing fails
    """
    try:
        if not Path(epub_path).exists():
            logger.error(
                "EPUB file not found", file_path=epub_path, operation="metadata_extraction"
            )
            raise FileNotFoundError(f"EPUB file not found: {epub_path}")

        # Read EPUB file
        logger.debug(
            "Starting EPUB metadata extraction",
            file_path=epub_path,
            operation="metadata_extraction",
        )
        book = epub.read_epub(epub_path)
        meta = {}

        # Standard metadata fields
        standard_fields = {
            "title": "title",
            "language": "language",
            "identifier": "identifier",
            "date": "date",
            "publisher": "publisher",
            "description": "description",
        }

        # Fields that may have multiple values
        multi_fields = ["creator", "contributor", "subject"]

        # Extract standard fields
        for field, dc_field in standard_fields.items():
            items = book.get_metadata("DC", dc_field)
            if items and len(items) > 0 and len(items[0]) > 0:
                meta[field] = items[0][0]

        # Handle multi-value fields
        for field in multi_fields:
            items = book.get_metadata("DC", field)
            if items:
                meta[field] = [item[0] for item in items]

        logger.info(
            "EPUB metadata extraction completed",
            file_path=epub_path,
            operation="metadata_extraction",
            metadata_fields=list(meta.keys()),
        )
        return meta

    except FileNotFoundError:
        raise FileNotFoundError(f"EPUB file not found: {epub_path}")
    except Exception as e:
        logger.error(
            "Failed to parse EPUB file",
            file_path=epub_path,
            operation="metadata_extraction",
            error_type=type(e).__name__,
            error_details=str(e),
        )
        raise EpubProcessingError("Failed to parse EPUB file", epub_path, "metadata_extraction", e)


@log_operation("epub_chapter_extraction")
def extract_chapter_from_epub(epub_path: str, anchor_href: str) -> str:
    """
    Extract complete HTML content of a chapter starting from specified chapter identifier.

    Args:
        epub_path: Complete path to the EPUB file
        anchor_href: Chapter location, title, or index (e.g. 'CHAPTER II', 'ch01.xhtml', or '5')

    Returns:
        HTML string of chapter content
    """
    logger.debug(
        "Starting EPUB chapter extraction",
        file_path=epub_path,
        anchor_href=anchor_href,
        operation="chapter_extraction",
    )
    book = epub.read_epub(epub_path)
    return extract_chapter_html(book, anchor_href)


def read_epub(epub_path: str) -> Any:
    return epub.read_epub(epub_path)


def flatten_toc(book: Any) -> list[str]:
    toc_list = []

    def _flatten(toc: Any) -> None:
        for item in toc:
            if isinstance(item, tuple):
                link, children = item
                toc_list.append(link.href)
                if children:
                    _flatten(children)
            else:
                # Handle single Link object
                toc_list.append(item.href)

    _flatten(book.toc)
    return toc_list


def extract_chapter_plain_text(book: Any, anchor_href: str) -> str:
    html = extract_chapter_html(book, anchor_href)
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text()


def convert_html_to_markdown(html_str: str) -> str:
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    return h.handle(html_str)


def clean_html(html_str: str) -> str:
    """
    Clean HTML content:
    - Remove unnecessary tags like <img>, <script>, <style>, <svg>, <video>, <iframe>, <nav>
    - Remove comments
    - Remove empty tags (like empty <p>)

    Returns:
    - Cleaned HTML string
    """
    soup = BeautifulSoup(html_str, "html.parser")

    # Remove unnecessary tags
    for tag in soup(["script", "style", "img", "svg", "iframe", "video", "nav"]):
        tag.decompose()

    # Remove HTML comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # Remove empty tags (no text and no useful attributes)
    for tag in soup.find_all():
        if not tag.get_text(strip=True) and not tag.find("img") and not tag.name == "br":
            tag.decompose()

    return str(soup)


def extract_chapter_html(book: Any, anchor_href: str) -> str:
    """
    Extract chapter HTML content with improved logic to handle subchapters correctly.
    Supports looking up chapters by href link, chapter title, or 1-based index.

    Args:
        book: EPUB book object
        anchor_href: Chapter identifier (href link, chapter title, or index)

    Returns:
        HTML string (complete chapter content with proper boundaries)
    """
    logger.debug(f"Extracting chapter with flexible matching: {anchor_href}")
    toc_entries = []
    for item in book.toc:
        if isinstance(item, tuple):
            chapter = item[0]
            toc_entries.append((chapter.title, chapter.href, 1))
            for sub_item in item[1]:
                if isinstance(sub_item, tuple):
                    toc_entries.append((sub_item[0].title, sub_item[0].href, 2))
                else:
                    toc_entries.append((sub_item.title, sub_item.href, 2))
        else:
            toc_entries.append((item.title, item.href, 1))

    current_idx = None
    target = anchor_href

    # 1. Check exact or partial match on toc_href
    for i, (title, toc_href, level) in enumerate(toc_entries):
        if toc_href == target or (target in toc_href and "#" in target):
            current_idx = i
            target = toc_href
            break

    # 2. Check exact or case-insensitive match on title
    if current_idx is None:
        target_clean = target.strip().lower()
        for i, (title, toc_href, level) in enumerate(toc_entries):
            if title.strip().lower() == target_clean:
                current_idx = i
                target = toc_href
                break

    # 3. Check partial / substring match on title
    if current_idx is None:
        target_clean = target.strip().lower()
        for i, (title, toc_href, level) in enumerate(toc_entries):
            title_clean = title.strip().lower()
            if target_clean in title_clean or title_clean in target_clean:
                current_idx = i
                target = toc_href
                break

    # 4. Check 1-based numeric index
    if current_idx is None and target.isdigit():
        idx = int(target) - 1
        if 0 <= idx < len(toc_entries):
            current_idx = idx
            title, toc_href, level = toc_entries[idx]
            target = toc_href

    if current_idx is None:
        raise EpubProcessingError(
            f"Chapter '{anchor_href}' not found in TOC", "unknown", "toc_lookup"
        )

    href, anchor = target.split("#") if "#" in target else (target, None)

    item = book.get_item_with_href(href)
    if item is None:
        raise EpubProcessingError(
            f"Chapter file not found: {href}", "unknown", "chapter_file_lookup"
        )

    soup = BeautifulSoup(item.get_content().decode("utf-8"), "html.parser")
    elems = []

    def heading_level(tag_name):
        if tag_name and tag_name.startswith("h") and tag_name[1:].isdigit():
            return int(tag_name[1:])
        return 7  # treat as lowest priority

    if anchor:
        start_elem = soup.find(id=anchor)
        if not start_elem:
            raise EpubProcessingError(
                f"Anchor {anchor} not found in {href}", "unknown", "anchor_lookup"
            )

        if start_elem.name in ("div", "section", "article", "main", "body"):
            html = str(start_elem)
        else:
            start_level = heading_level(start_elem.name)
            elems = [str(start_elem)]
            for elem in start_elem.next_siblings:
                if (
                    hasattr(elem, "name")
                    and elem.name
                    and elem.name.startswith("h")
                    and elem.name[1:].isdigit()
                ):
                    if heading_level(elem.name) <= start_level:
                        break
                elems.append(str(elem))
            html = "\n".join(elems)
    else:
        chapter_elem = soup.find(["h1", "h2", "h3", "h4", "h5", "h6"])
        if chapter_elem:
            start_level = heading_level(chapter_elem.name)
            elems = [str(chapter_elem)]
            for elem in chapter_elem.next_siblings:
                if (
                    hasattr(elem, "name")
                    and elem.name
                    and elem.name.startswith("h")
                    and elem.name[1:].isdigit()
                ):
                    if heading_level(elem.name) <= start_level:
                        break
                elems.append(str(elem))
            html = "\n".join(elems)
        else:
            body_elem = soup.find("body")
            html = str(body_elem) if body_elem else str(soup)

    return clean_html(html)


def extract_chapter_markdown(book: Any, anchor_href: str) -> str:
    """Fixed version of extract_chapter_markdown using extract_chapter_html"""
    html = extract_chapter_html(book, anchor_href)
    return convert_html_to_markdown(html)


def extract_multiple_chapters(
    book: Any, anchor_list: list[str], output: str = "html"
) -> list[tuple[str, str]]:
    """Extract multiple chapters using improved extract_chapter_html logic"""
    results = []
    for href in anchor_list:
        if output == "html":
            content = extract_chapter_html(book, href)
        elif output == "text":
            content = extract_chapter_plain_text(book, href)
        elif output == "markdown":
            content = extract_chapter_markdown(book, href)
        else:
            raise ValueError("Invalid output format.")
        results.append((href, content))
    return results
