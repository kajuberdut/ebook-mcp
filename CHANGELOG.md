# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### 🔧 Fixed
- **EPUB Container Element Extraction**: Fixed a bug in `extract_chapter_html` where anchor targets pointing to wrapper container elements (such as `<div class="chapter" id="...">`) were prematurely truncated after line 1 due to `next_elements` DOM iteration encountering internal `<h2>` headings. Switched to container-aware node evaluation and `next_siblings` DOM traversal.
- **EPUB Chapter Identifier Resolution**: Updated `get_epub_chapter_markdown` and `extract_chapter_html` in `epub_helper.py` to support chapter lookup by exact or partial chapter title (e.g. `'CHAPTER II. The Pool of Tears'`), href link, or 1-based index (e.g. `'5'`), enabling seamless tool chaining with `get_epub_toc`.

- **CLI Entry Point**: Fixed `cli_entry()` in `main.py` to run the module-level `FastMCP` server with all registered tools instead of instantiating an empty server

- **Module Execution**: Added `__main__.py` to support launching server via `python -m ebook_mcp`

### 🗑️ Removed
- **PDF Support Removal**: Removed all PDF processing dependencies (`PyMuPDF`), module helpers (`pdf_helper.py`), tool endpoints (`get_all_pdf_files`, `get_pdf_metadata`, `get_pdf_toc`, `get_pdf_page_text`, `get_pdf_page_markdown`, `get_pdf_chapter_content`), and unit tests (`test_pdf_helper.py`) to focus `ebook-mcp` strictly on EPUB e-books.

### 🔒 Security

- **Unsafe Defaults Warning**: Added explicit runtime `logger.warning()` alerts in `cli_entry()` when FastMCP runs with wildcard allowed hosts/origins (`*`) or unconstrained file boundary directory settings (`EBOOK_MCP_ALLOWED_DIR` unset).
- **DNS Rebinding & Transport Security Controls**: Configured `allowed_hosts` and `allowed_origins` in `cli_entry()` (with `EBOOK_MCP_ALLOWED_HOSTS` and `EBOOK_MCP_ALLOWED_ORIGINS` env var support) so FastMCP accepts container hostnames like `ebook-mcp-server` over SSE network transport without `421 Misdirected Request` errors.
- **Path Traversal Protection & Security Validation**: Added `src/ebook_mcp/tools/security.py` module to resolve paths safely, enforce extension whitelists (`.epub`, `.pdf`), validate parameter bounds (`page_number >= 1`), and enforce optional directory scoping via `EBOOK_MCP_ALLOWED_DIR`.

### 🌟 Added
- **Pytest Coverage Expansion**: Enhanced unit test suite to achieve **91% overall test coverage** (100% `security.py`, 100% `__main__.py`, 100% `docker_cli.py`, 99% `main.py`, 94% `epub_helper.py`), adding test coverage for FastMCP prompt templates, `get_epub_chapter_markdown`, `cli_entry` transport modes, and EPUB helper error handling.

- **Vulture Dead Code Checking**: Integrated `vulture` dead-code analyzer into `dev` dependencies, created `.vulture_whitelist.py` for FastMCP framework entrypoints, and configured `poe vulture` task in `pyproject.toml`.

- **MCP Inspector Tutorial**: Added [`docs/tutorials/using_mcp_inspector.md`](docs/tutorials/using_mcp_inspector.md) covering high-level MCP concepts, running `uv run poe compose-inspector`, navigating the Tools tab, and executing the 3-step e-book discovery walkthrough with 4-tier flexible chapter matching.

- **MCP Config Directory & Auto-Injection**: Moved client config preset to `.mcp/mcp.json` and mounted `./.mcp/mcp.json:/app/mcp.json:ro` into the Inspector container (`--config /app/mcp.json`) for seamless zero-manual-setup debugging.

- **Out-of-the-Box Public Domain Sample EPUB**: Added *Alice's Adventures in Wonderland* (`sample_books/alice_in_wonderland.epub`) by Lewis Carroll and configured `docker-compose.yml` to mount `./sample_books:/library:ro` for instant out-of-the-box testing.
- **MCP Inspector Compose Override**: Added `docker-compose.inspector.yml` mix-in file bundling the official `@modelcontextprotocol/inspector` on ports 5173/3000.


- **Poe Compose Automation Tasks**: Configured `poe compose up`, `poe compose inspector`, `poe compose-up`, and `poe compose-inspector` tasks in `pyproject.toml` with dispatch helper `src/ebook_mcp/tools/docker_cli.py`.
- **Multi-Stage Secure Dockerfile**: Created efficient multi-stage build (`Dockerfile`) using `ghcr.io/astral-sh/uv` builder stage and `python:3.12-slim-bookworm` runtime stage with non-root system user (`ebookmcp`), security options, and automated SSE health checks.
- **Docker Compose Orchestration**: Created `docker-compose.yml` allowing e-book library mounting (`./library:/library:ro`), log persistence (`ebook-mcp-logs`), capabilities dropping (`cap_drop: [ALL]`), and `no-new-privileges` security flags.

- **Docker Build Context Optimization**: Added `.dockerignore` to exclude cache, venvs, and development files from Docker build context.
- **FastMCP 3.x Server Instructions**: Added server-level AI instructions to `FastMCP("ebook-mcp", instructions=...)` guiding LLM tools usage.
- **Native FastMCP Prompts**: Added `@mcp.prompt()` templates for `summarize_chapter` and `generate_quiz`.
- **Docker/SSE Transport Flexibility**: Updated `cli_entry()` to support running over SSE/HTTP (`EBOOK_MCP_TRANSPORT=sse`, `EBOOK_MCP_HOST`, `EBOOK_MCP_PORT`) as well as standard `stdio`.
- **Developer Tooling**: Added `ruff` and `poethepoet` to dev optional-dependencies in `pyproject.toml`
- **Task Automation**: Configured `poe` tasks for `lint`, `lint-fix`, `format`, `format-check`, `check`, and `test`



### 🔧 Refactored
- **Python 3.12 Target Upgrade**: Upgraded `requires-python = ">=3.12"` and Ruff target version `py312` in `pyproject.toml`
- **Modern Python 3.12 Type Hints (PEP 585 / 604 / 695)**: Upgraded legacy `typing` annotations (`List`, `Tuple`, `Dict`, `Union`, `Optional`) to native built-ins (`list`, `tuple`, `dict`, `A | B`, `A | None`), and adopted PEP 695 generic function syntax (`def func[T](...)`)
- **Exception Handling Safety**: Modernized bare `except:` blocks in `pdf_helper.py` to explicit `except Exception:` catches
- **Cross-Platform Directory Resolution**: Integrated `platformdirs>=4.11.3` for standard Linux XDG state directory path resolution (`platformdirs.user_state_dir("ebook-mcp")`)

- **Complete Repository Pathlib Adoption**: Refactored 100% of file system operations, path manipulation, and test suites across the repository to use `pathlib.Path` instead of legacy `os.path`, `os.listdir`, and `os.unlink`

- **Opinionated Linux Logging**: Implemented XDG state directory specification (`$XDG_STATE_HOME/ebook-mcp/logs` / `~/.local/state/ebook-mcp/logs`) with `EBOOK_MCP_LOG_DIR` environment variable support
- **MCP Transport Compatibility**: Directed console stream handler to `sys.stderr` to prevent MCP stdio protocol JSON-RPC corruption
- **Import Side-Effect Elimination**: Deferred logger directory creation and handler setup to `cli_entry()` to guarantee side-effect free module imports


- **English Localization**: Translated `HOW-TO-TEST.md` and `run_tests.sh` to English

### 🗑️ Removed
- **Non-English Resources**: Removed localized README files (`README-CN.md`, `README-DE.md`, `README-FR.md`, `README-JP.md`, `README-KR.md`, `mcp_client_example/README-CN.md`) and translation hook `.kiro/hooks/readme-translation-hook.kiro.hook`
- **Leftover Backup File**: Removed leftover source backup file `src/ebook_mcp/tools/pdf_helper.py.backup`
- **Orphaned Test**: Removed non-existent module test `src/ebook_mcp/tests/test_azw.py`





### 🔧 Refactored
- **Modernized Dependency Management**: Removed `requirements.txt`, fully using `pyproject.toml` for dependency management
  - Deleted `requirements.txt` file
  - Updated installation instructions in all README files
  - Unified use of modern Python package management standards
  - Simplified installation process: `uv pip install -e .` or `pip install -e .`

- **PDF Processing Optimization**: Removed `PyPDF2` dependency, fully using `PyMuPDF`
  - Removed `PyPDF2` imports and `get_meta_pypdf2` function from `pdf_helper.py`
  - Updated `pyproject.toml`, removed `PyPDF2` dependency
  - Deleted `test_pdf_metadata_comparison.py` test file
  - Updated related tests, removed `PyPDF2` related tests

  - Enhanced PDF metadata extraction functionality, providing richer metadata information

### 🌍 Added
- **Internationalization Support**: Added multilingual README documentation
  - Added German README (`README-DE.md`)
  - Added French README (`README-FR.md`)
  - Added Japanese README (`README-JP.md`)
  - Added Korean README (`README-KR.md`)
  - Added Kiro translation tool configuration (`.kiro/hooks/readme-translation-hook.kiro.hook`)

### 🔧 Technical Improvements
- **Dependency Management**: Compliant with modern Python project standards (PEP 518/621)
- **PDF Processing**: Improved performance and stability, reduced dependency conflicts
- **Test Coverage**: All tests passing (76 passed, 5 skipped)
- **Code Quality**: Simplified code structure, improved maintainability

### 📝 Documentation
- Updated installation instructions in all README files
- Added multilingual support documentation
- Updated MCP client example documentation
- Improved project documentation accessibility

### 🗑️ Removed
- `requirements.txt` file
- `PyPDF2` dependency and related code
- `test_pdf_metadata_comparison.py` test file
- Outdated installation instruction references

### 🔄 Backward Compatibility
- ✅ Maintained API compatibility, no need to modify existing code
- ✅ All MCP tools working normally
- ✅ Functional integrity guaranteed

### 📦 Installation Instructions
```bash
# Development environment
git clone <repository-url>
cd ebook-mcp
uv pip install -e .
# or
pip install -e .

# Run tests
./run_tests.sh
# or
pytest src/ebook_mcp/tests/
```

### 🎯 Impact Assessment
- **Positive Impact**:
  - Simplified dependency management
  - Improved PDF processing performance
  - Enhanced internationalization support
  - Reduced maintenance complexity
  - Compliant with modern Python project standards

- **Potential Impact**:
  - Users need to update installation methods
  - Removed specific PyPDF2 features (replaced by PyMuPDF)

### 🔄 Migration Guide
For existing users:
1. Delete `requirements.txt` file (if exists)
2. Reinstall using `uv pip install -e .`
3. Update CI/CD configuration (if using requirements.txt)

---

## [0.1.4] - 2025-08-05

### 🔧 Fixed
- Fixed subchapter truncation issue in EPUB chapter extraction
- Added `get_epub_chapter_markdown_fixed` tool
- Improved chapter boundary detection logic
- Updated related tests and documentation

### 📝 Documentation
- Added `HOW-TO-TEST.md` testing documentation
- Updated test runner scripts
- Improved error handling and logging

## [0.1.3] - 2025-08-04

### 🌟 Added
- Added comprehensive unit test suite
- Created test configuration files and runner scripts
- Added test documentation and examples

### 🔧 Improved
- Improved error handling mechanisms
- Optimized code structure and readability
- Enhanced test coverage

## [0.1.2] - 2025-08-03

### 🌟 Added
- Added PDF chapter content extraction functionality
- Support for extracting content by chapter title
- Added Markdown format output support

### 🔧 Improved
- Optimized PDF metadata extraction
- Improved error handling
- Updated API documentation

## [0.0.1] - 2025-08-02

### 🔧 Fixed
- Fixed compatibility issues in PDF processing
- Improved EPUB metadata extraction
- Optimized file path handling

### 📝 Documentation
- Updated installation instructions
- Added usage examples
- Improved API documentation

## [1.0.0] - 2025-08-01

### 🌟 Initial Release
- EPUB and PDF format support
- Basic file processing APIs
- MCP client examples - Claude, DeepSeek, OpenAI
- Support for running server from PyPI
- Basic metadata extraction functionality
- Table of contents extraction support
- Chapter content extraction functionality

---

## Version Notes

### Semantic Versioning
- **Major version**: Incompatible API changes
- **Minor version**: Backward-compatible functionality additions
- **Patch version**: Backward-compatible bug fixes

### Change Types
- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Features that will be removed soon
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security improvements 