# Epub-MCP Unit Testing Guide

This guide explains how to run unit tests for the server components of the `epub-mcp` project.

## Test Directory Structure

```
src/epub_mcp/tests/
├── conftest.py              # pytest configuration and shared fixtures
├── test_main.py             # Unit tests for main.py
├── test_epub_helper.py      # Unit tests for epub_helper.py
└── test_security.py         # Unit tests for security path validation
```

## Test Coverage

### main.py Tests
- EPUB tools tests:
  - `get_all_epub_files`
  - `get_epub_metadata`
  - `get_epub_toc`
  - `get_epub_chapter_markdown`
- Error handling tests:
  - File non-existence
  - Parsing errors
  - Exception propagation

### epub_helper.py Tests
- File operations
- EPUB parsing
- Table of contents processing
- HTML cleaning and conversion
- Flexible chapter extraction (title, href, index)


## Running Tests

### Method 1: Using Poe Task Runner (Recommended)

```bash
# Run all unit tests with terminal missing coverage report
uv run poe test

# Run tests and generate HTML coverage report (in htmlcov/ directory)
uv run poe coverage

# Run code check & format verification (ruff + vulture)
uv run poe check

# Run code linting (ruff)
uv run poe lint
```


### Method 2: Using pytest directly

```bash
# Run all tests
pytest src/epub_mcp/tests/ -v

# Run specific test file
pytest src/epub_mcp/tests/test_main.py -v

# Run specific test class
pytest src/epub_mcp/tests/test_main.py::TestEpubFunctions -v

# Run specific test method
pytest src/epub_mcp/tests/test_main.py::TestEpubFunctions::test_get_all_epub_files_empty_directory -v
```

### Method 3: Running with uv

```bash
# Run all tests
uv run pytest src/epub_mcp/tests/ -v

# Run specific test
uv run pytest src/epub_mcp/tests/test_main.py -v
```


### Method 4: Using Test Runner Script

```bash
# Run all tests
python src/ebook_mcp/tests/run_tests.py

# List all test files
python src/ebook_mcp/tests/run_tests.py list

# Run specific test file
python src/ebook_mcp/tests/run_tests.py run test_main.py
```

## Test Environment Requirements

### Basic Dependencies
Ensure the following dependencies are installed:

```bash
# Using pip
pip install -e .[dev]

# Using uv
uv sync --extra dev
```

## Test Output Examples

### Successful Run Example
```
Running ebook-mcp unit tests...
==================================================
test_main.py::TestEpubFunctions::test_get_all_epub_files_empty_directory PASSED
test_main.py::TestEpubFunctions::test_get_all_epub_files_with_epub_files PASSED
test_main.py::TestEpubFunctions::test_get_epub_metadata_success PASSED
...
test_pdf_helper.py::TestPdfHelper::test_get_all_pdf_files_empty_directory PASSED
test_pdf_helper.py::TestPdfHelper::test_get_all_pdf_files_with_pdf_files PASSED
...

==================================================
✅ All tests passed!
```

## Test Strategy

### Unit Testing Principles
1. **Isolation**: Each test is independent and does not rely on other tests.
2. **Repeatability**: Tests can be executed consistently in any environment.
3. **Speed**: Fast execution times.
4. **Completeness**: Covers both success paths and error cases.

### Mock Usage
- Uses `unittest.mock` to isolate external dependencies.
- Mocks file system operations.
- Mocks EPUB and PDF parsing libraries.

## Debugging Tests

```bash
# Run tests with verbose output
pytest src/ebook_mcp/tests/ -v -s

# Stop on first failure
pytest src/ebook_mcp/tests/ -x

# Show local variables on failure
pytest src/ebook_mcp/tests/ --tb=long
```
