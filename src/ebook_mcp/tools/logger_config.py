import json
import logging
import os
import tempfile
import time
import traceback
from datetime import datetime
from functools import wraps
from pathlib import Path


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""

    def format(self, record: logging.LogRecord) -> str:
        # Create structured log entry
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "file_path"):
            log_entry["file_path"] = record.file_path
        if hasattr(record, "operation"):
            log_entry["operation"] = record.operation
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms
        if hasattr(record, "file_size"):
            log_entry["file_size"] = record.file_size
        if hasattr(record, "page_count"):
            log_entry["page_count"] = record.page_count
        if hasattr(record, "chapter_count"):
            log_entry["chapter_count"] = record.chapter_count
        if hasattr(record, "error_type"):
            log_entry["error_type"] = record.error_type
        if hasattr(record, "error_details"):
            log_entry["error_details"] = record.error_details

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_entry, ensure_ascii=False, default=str)


class StructuredLogger:
    """Enhanced logger with structured logging capabilities"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.name = name

    def _log_with_context(self, level: int, message: str, **context):
        """Log with additional context fields"""
        # Check if we're in a test environment
        import sys

        if "pytest" in sys.modules or "test" in self.name:
            # Skip logging in test environment
            return

        extra = {}
        for key, value in context.items():
            if value is not None:
                extra[key] = value

        self.logger.log(level, message, extra=extra)

    def info(self, message: str, **context):
        """Log info message with context"""
        self._log_with_context(logging.INFO, message, **context)

    def debug(self, message: str, **context):
        """Log debug message with context"""
        self._log_with_context(logging.DEBUG, message, **context)

    def warning(self, message: str, **context):
        """Log warning message with context"""
        self._log_with_context(logging.WARNING, message, **context)

    def error(self, message: str, **context):
        """Log error message with context"""
        self._log_with_context(logging.ERROR, message, **context)

    def critical(self, message: str, **context):
        """Log critical message with context"""
        self._log_with_context(logging.CRITICAL, message, **context)


def get_default_log_dir() -> str:
    """Get opinionated Linux log directory using XDG state specification.

    1. EBOOK_MCP_LOG_DIR environment variable (if set)
    2. $XDG_STATE_HOME/ebook-mcp/logs (defaulting to ~/.local/state/ebook-mcp/logs)
    3. Fallback to temp directory if target directory is not writable
    """
    env_dir = os.getenv("EBOOK_MCP_LOG_DIR")
    if env_dir:
        log_dir = Path(env_dir)
    else:
        xdg_state = os.getenv("XDG_STATE_HOME", str(Path.home() / ".local" / "state"))
        log_dir = Path(xdg_state) / "ebook-mcp" / "logs"

    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        return str(log_dir)
    except (PermissionError, OSError):
        temp_dir = Path(tempfile.gettempdir()) / "ebook-mcp" / "logs"
        temp_dir.mkdir(parents=True, exist_ok=True)
        return str(temp_dir)


def setup_logger(level: str = None, log_file: str = None):
    """Configure structured logging system for Linux and MCP stdio transport.

    - Log level defaults to EBOOK_MCP_LOG_LEVEL or 'INFO'
    - Console logs explicitly stream to sys.stderr to prevent stdio MCP protocol corruption
    - File logs output JSON-structured entries to XDG log dir or EBOOK_MCP_LOG_DIR
    """
    import sys

    if level is None:
        level = os.getenv("EBOOK_MCP_LOG_LEVEL", "INFO")

    if log_file is None:
        log_file = f"ebook_mcp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    log_dir = get_default_log_dir()
    log_file_path = os.path.join(log_dir, log_file)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create formatters
    structured_formatter = StructuredFormatter()
    console_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # File handler with structured JSON logging
    try:
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setFormatter(structured_formatter)
        file_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
    except (PermissionError, OSError):
        pass

    # Console handler MUST explicitly stream to sys.stderr to prevent stdio MCP protocol corruption
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
    root_logger.addHandler(console_handler)

    return root_logger


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance"""
    return StructuredLogger(name)


def log_operation(operation_name: str):
    """Decorator to log operation start/end with timing"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if we're in a test environment by looking for pytest
            import sys

            if "pytest" in sys.modules or "test" in func.__module__:
                # Skip logging in test environment
                return func(*args, **kwargs)

            logger = get_logger(func.__module__)
            start_time = time.time()

            # Log operation start
            logger.info(
                f"Starting {operation_name}", operation=operation_name, function=func.__name__
            )

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000

                # Log operation success
                logger.info(
                    f"Completed {operation_name} successfully",
                    operation=operation_name,
                    function=func.__name__,
                    duration_ms=round(duration_ms, 2),
                )

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000

                # Log operation failure
                logger.error(
                    f"Failed to complete {operation_name}",
                    operation=operation_name,
                    function=func.__name__,
                    duration_ms=round(duration_ms, 2),
                    error_type=type(e).__name__,
                    error_details=str(e),
                )
                raise

        return wrapper

    return decorator
