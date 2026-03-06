#!/usr/bin/env python3
"""Script to run tests inside Docker container."""

import subprocess
import sys

def run_command(cmd, description):
    """Run a command and print results."""
    print(f"\n{'='*50}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def main():
    """Run tests with different configurations."""
    
    # Check if we're inside Docker container
    try:
        with open('/proc/1/cgroup', 'r') as f:
            if 'docker' in f.read():
                # We're inside container, run pytest directly
                base_cmd = "pytest"
            else:
                # We're outside container, use docker exec
                base_cmd = "docker exec -it chat_api pytest"
    except FileNotFoundError:
        # Probably Windows or not in container
        base_cmd = "docker exec -it chat_api pytest"
    
    # Test configurations
    tests = [
        (f"{base_cmd} -v", "All tests with verbose output"),
        (f"{base_cmd} tests/test_chat_unit.py -v", "Unit tests only"),  
        (f"{base_cmd} tests/test_chat_integration.py -v", "Integration tests only"),
        (f"{base_cmd} --cov=app --cov-report=term-missing", "Tests with coverage report"),
    ]
    
    success_count = 0
    
    for cmd, description in tests:
        if run_command(cmd, description):
            success_count += 1
        else:
            print(f"❌ Failed: {description}")
    
    print(f"\n{'='*60}")
    print(f"Summary: {success_count}/{len(tests)} test suites passed")
    print(f"{'='*60}")
    
    if success_count == len(tests):
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()