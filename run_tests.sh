#!/bin/bash

# Ebook-MCP Test Runner Script

echo "=========================================="
echo "Ebook-MCP Unit Test Runner"
echo "=========================================="

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest is not installed. Please install it first: pip install pytest"
    exit 1
fi

# Set test directory
TEST_DIR="src/ebook_mcp/tests"

echo "📁 Test directory: $TEST_DIR"
echo ""

# Run basic tests
echo "🧪 Running basic tests..."
python -m pytest $TEST_DIR/test_basic.py -v
BASIC_RESULT=$?

echo ""
echo "🧪 Running EPUB chapter extraction tests..."
python -m pytest $TEST_DIR/test_epub_chapter_extraction.py -v
FIXED_RESULT=$?

# Return overall result
if [ $BASIC_RESULT -eq 0 ] && [ $FIXED_RESULT -eq 0 ]; then
    echo "🎉 All available tests passed!"
    exit 0
else
    echo "⚠️  Some tests failed. Please check the output above."
    exit 1
fi
