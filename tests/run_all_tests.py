#!/usr/bin/env python3
"""Run all API tests."""

import os
import subprocess
import sys
import time

def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 30 + f" {title} " + "=" * 30 + "\n")

def run_test(test_file):
    """Run a test file and return success status."""
    print_header(f"Running {test_file}")
    
    result = subprocess.run([sys.executable, test_file], capture_output=False)
    
    return result.returncode == 0

def main():
    """Run all tests."""
    # Change to the tests directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print_header("xAI API TESTS")
    
    test_files = [
        "test_direct_api.py",
        "test_openai_sdk.py"
    ]
    
    results = {}
    
    for test_file in test_files:
        results[test_file] = run_test(test_file)
        # Add a small delay between tests
        time.sleep(2)
    
    # Print summary
    print_header("TEST RESULTS SUMMARY")
    
    for test_file, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_file}: {status}")
    
    # Return success only if all tests passed
    return 0 if all(results.values()) else 1

if __name__ == "__main__":
    sys.exit(main()) 