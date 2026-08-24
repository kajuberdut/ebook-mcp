import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from ebook_mcp.tools.security import (
    SecurityValidationError,
    validate_file_path,
)


def test_validate_file_path_success():
    with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
        f.write(b"content")
        temp_path = f.name

    try:
        resolved = validate_file_path(temp_path, allowed_extensions={".epub"})
        assert resolved == Path(temp_path).resolve()
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_validate_file_path_not_found():
    with pytest.raises(FileNotFoundError):
        validate_file_path("/nonexistent/path/book.epub")


def test_validate_file_path_invalid_extension():
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"content")
        temp_path = f.name

    try:
        with pytest.raises(SecurityValidationError, match="Invalid file extension"):
            validate_file_path(temp_path, allowed_extensions={".epub"})
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_validate_file_path_allowed_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        allowed_path = Path(temp_dir) / "allowed"
        allowed_path.mkdir()
        forbidden_path = Path(temp_dir) / "forbidden"
        forbidden_path.mkdir()

        good_file = allowed_path / "book.epub"
        good_file.write_text("epub")

        bad_file = forbidden_path / "book.epub"
        bad_file.write_text("epub")

        with patch.dict("os.environ", {"EBOOK_MCP_ALLOWED_DIR": str(allowed_path)}):
            assert (
                validate_file_path(good_file, allowed_extensions={".epub"}) == good_file.resolve()
            )

            with pytest.raises(SecurityValidationError, match="Access denied"):
                validate_file_path(bad_file, allowed_extensions={".epub"})


def test_validate_file_path_not_regular_file():
    with tempfile.TemporaryDirectory() as temp_dir:
        with pytest.raises(SecurityValidationError, match="Target path is not a regular file"):
            validate_file_path(temp_dir, must_exist=True)
