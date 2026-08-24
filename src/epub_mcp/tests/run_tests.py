#!/usr/bin/env python3
"""
Test runner script for epub-mcp project.
This script runs all unit tests for the server components.
"""

import sys
from pathlib import Path

import pytest

THIS_DIR = Path(__file__).resolve().parent
SRC_DIR = THIS_DIR.parent.parent


def run_tests():
    """Run all tests for the epub-mcp project"""

    # Add the src directory to Python path
    sys.path.insert(0, str(SRC_DIR))

    print("Running epub-mcp unit tests...")
    print("=" * 50)

    # Run tests with pytest
    try:
        # Run tests with verbose output and coverage
        result = pytest.main(
            [str(THIS_DIR), "-v", "--tb=short", "--strict-markers", "--disable-warnings"]
        )

        if result == 0:
            print("\n" + "=" * 50)
            print("✅ All tests passed!")
            return True
        else:
            print("\n" + "=" * 50)
            print("❌ Some tests failed!")
            return False

    except Exception as e:
        print(f"Error running tests: {e}")
        return False


def run_specific_test(test_file):
    """Run a specific test file"""
    sys.path.insert(0, str(SRC_DIR))

    test_path = THIS_DIR / test_file

    print(f"Running specific test: {test_file}")
    print("=" * 50)

    try:
        result = pytest.main([str(test_path), "-v", "--tb=short"])

        if result == 0:
            print("\n" + "=" * 50)
            print("✅ Test passed!")
            return True
        else:
            print("\n" + "=" * 50)
            print("❌ Test failed!")
            return False

    except Exception as e:
        print(f"Error running test: {e}")
        return False


def list_tests():
    """List all available test files"""
    test_files = [f.name for f in THIS_DIR.glob("test_*.py") if f.is_file()]

    print("Available test files:")
    print("=" * 30)
    for test_file in sorted(test_files):
        print(f"  - {test_file}")

    return test_files


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "list":
            list_tests()
        elif command == "run":
            if len(sys.argv) > 2:
                test_file = sys.argv[2]
                run_specific_test(test_file)
            else:
                run_tests()
        else:
            print("Usage:")
            print("  python run_tests.py list          - List all test files")
            print("  python run_tests.py run           - Run all tests")
            print("  python run_tests.py run test_file - Run specific test file")
    else:
        run_tests()
