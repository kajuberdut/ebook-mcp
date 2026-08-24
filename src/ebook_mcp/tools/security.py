import os
from pathlib import Path


class SecurityValidationError(ValueError):
    """Exception raised when path resolution or input validation fails security constraints."""

    pass


def validate_file_path(
    path: str | Path,
    allowed_extensions: set[str] | None = None,
    must_exist: bool = True,
) -> Path:
    """Validate and resolve file path for security constraints.

    1. Resolves path to absolute path.
    2. Checks file existence (if must_exist is True).
    3. Validates file extension against allowed_extensions whitelist.
    4. Enforces EBOOK_MCP_ALLOWED_DIR boundary check if EBOOK_MCP_ALLOWED_DIR env var is set.
    """
    resolved = Path(path).resolve()

    if must_exist and not resolved.exists():
        raise FileNotFoundError(f"File not found: {resolved}")

    if must_exist and not resolved.is_file():
        raise SecurityValidationError(f"Target path is not a regular file: {resolved}")

    if allowed_extensions:
        ext = resolved.suffix.lower()
        if ext not in allowed_extensions:
            allowed_str = ", ".join(sorted(allowed_extensions))
            raise SecurityValidationError(
                f"Invalid file extension '{ext}'. Allowed extensions: {allowed_str}"
            )

    allowed_dir_env = os.getenv("EBOOK_MCP_ALLOWED_DIR")
    if allowed_dir_env:
        allowed_root = Path(allowed_dir_env).resolve()
        try:
            resolved.relative_to(allowed_root)
        except ValueError:
            raise SecurityValidationError(
                f"Access denied: path '{resolved}' is outside allowed directory '{allowed_root}'"
            )

    return resolved
