#!/usr/bin/env python3
"""
Test runner script for EnvDoc
Provides convenient test execution with coverage reporting
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Exit code: {e.returncode}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Run EnvDoc tests")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage")
    parser.add_argument("--lint", action="store_true", help="Run linting")
    parser.add_argument("--type-check", action="store_true", help="Run type checking")
    parser.add_argument("--all", action="store_true", help="Run all quality checks")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.all:
        args.coverage = args.lint = args.type_check = True
    
    success = True
    
    # Change to package directory
    os.chdir(Path(__file__).parent)
    
    # Run linting
    if args.lint:
        lint_cmd = [
            sys.executable, "-m", "flake8", "envdoc/", 
            "--count", "--statistics"
        ]
        if not run_command(lint_cmd, "Linting"):
            success = False
    
    # Run type checking
    if args.type_check:
        mypy_cmd = [
            sys.executable, "-m", "mypy", "envdoc/", 
            "--ignore-missing-imports", "--no-strict-optional"
        ]
        if not run_command(mypy_cmd, "Type checking"):
            success = False
    
    # Run tests
    test_cmd = [sys.executable, "-m", "pytest", "tests/"]
    
    if args.verbose:
        test_cmd.append("-v")
    
    if args.coverage:
        test_cmd.extend([
            "--cov=envdoc",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-fail-under=80"
        ])
    
    if not run_command(test_cmd, "Unit tests"):
        success = False
    
    # Summary
    if success:
        print("\n🎉 All tests and checks passed!")
        sys.exit(0)
    else:
        print("\n💥 Some tests or checks failed!")
        sys.exit(1)


if __name__ == "__main__":
    import os
    main()
