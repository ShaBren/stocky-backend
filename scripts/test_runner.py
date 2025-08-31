#!/usr/bin/env python3
"""
Test runner script for Stocky Backend.

This script provides a convenient way to run different test categories
and generate reports.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: str, cwd: Path = None) -> int:
    """Run a shell command and return the exit code."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    return result.returncode


def run_tests(category: str = "all", coverage: bool = False, verbose: bool = False) -> int:
    """Run tests with specified options."""
    
    base_cmd = "pytest"
    
    # Add verbosity
    if verbose:
        base_cmd += " -v"
    
    # Add coverage
    if coverage:
        base_cmd += " --cov=src/stocky_backend --cov-report=html --cov-report=term-missing"
    
    # Select test category
    if category == "unit":
        cmd = f"{base_cmd} tests/unit/"
    elif category == "integration":
        cmd = f"{base_cmd} tests/integration/"
    elif category == "api":
        cmd = f"{base_cmd} tests/api/"
    elif category == "e2e":
        cmd = f"{base_cmd} tests/e2e/"
    elif category == "auth":
        cmd = f"{base_cmd} -m auth"
    elif category == "database":
        cmd = f"{base_cmd} -m database"
    elif category == "slow":
        cmd = f"{base_cmd} -m slow"
    else:  # all
        cmd = base_cmd
    
    return run_command(cmd)


def setup_test_environment() -> int:
    """Set up the test environment."""
    print("Setting up test environment...")
    
    commands = [
        "pip install -r tests/requirements-test.txt",
        "pip install -e ."
    ]
    
    for cmd in commands:
        if run_command(cmd) != 0:
            return 1
    
    print("Test environment setup complete!")
    return 0


def lint_code() -> int:
    """Run linting checks."""
    print("Running linting checks...")
    
    commands = [
        "flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics",
        "flake8 src/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics"
    ]
    
    for cmd in commands:
        if run_command(cmd) != 0:
            return 1
    
    return 0


def type_check() -> int:
    """Run type checking."""
    print("Running type checks...")
    return run_command("mypy src/ --ignore-missing-imports")


def security_scan() -> int:
    """Run security scans."""
    print("Running security scans...")
    
    commands = [
        "safety check",
        "bandit -r src/"
    ]
    
    for cmd in commands:
        if run_command(cmd) != 0:
            print(f"Warning: {cmd} failed, but continuing...")
    
    return 0


def generate_report() -> int:
    """Generate test and coverage reports."""
    print("Generating reports...")
    
    # Run tests with coverage
    cmd = "pytest --cov=src/stocky_backend --cov-report=html --cov-report=xml --cov-report=term-missing --html=report.html --self-contained-html"
    
    result = run_command(cmd)
    
    if result == 0:
        print("\nReports generated:")
        print("- Coverage: htmlcov/index.html")
        print("- Test Report: report.html")
    
    return result


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Stocky Backend Test Runner")
    
    parser.add_argument(
        "command",
        choices=["test", "setup", "lint", "type-check", "security", "report", "all"],
        help="Command to run"
    )
    
    parser.add_argument(
        "--category",
        choices=["all", "unit", "integration", "api", "e2e", "auth", "database", "slow"],
        default="all",
        help="Test category to run (only applies to 'test' command)"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Include coverage reporting"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    if args.command == "setup":
        return setup_test_environment()
    
    elif args.command == "test":
        return run_tests(args.category, args.coverage, args.verbose)
    
    elif args.command == "lint":
        return lint_code()
    
    elif args.command == "type-check":
        return type_check()
    
    elif args.command == "security":
        return security_scan()
    
    elif args.command == "report":
        return generate_report()
    
    elif args.command == "all":
        # Run complete test suite
        commands = [
            ("Setup", lambda: setup_test_environment()),
            ("Linting", lambda: lint_code()),
            ("Type Checking", lambda: type_check()),
            ("Unit Tests", lambda: run_tests("unit", True)),
            ("Integration Tests", lambda: run_tests("integration", True)),
            ("API Tests", lambda: run_tests("api", True)),
            ("Security Scan", lambda: security_scan()),
        ]
        
        for name, func in commands:
            print(f"\n{'='*50}")
            print(f"Running {name}")
            print('='*50)
            
            if func() != 0:
                print(f"{name} failed!")
                return 1
        
        print(f"\n{'='*50}")
        print("All checks passed!")
        print('='*50)
        return 0
    
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
