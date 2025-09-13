#!/usr/bin/env python3
"""
Project cleanup utility for telematics system.
This script helps clean up temporary files, logs, and other artifacts.
"""

import os
import shutil
import glob

def cleanup_logs():
    """Remove log files and temporary data."""
    log_patterns = [
        "**/*.log",
        "**/logs/**",
        "**/__pycache__/**",
        "**/.pytest_cache/**",
        "**/tmp/**",
        "**/temp/**"
    ]
    
    for pattern in log_patterns:
        for file_path in glob.glob(pattern, recursive=True):
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"Removed file: {file_path}")
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    print(f"Removed directory: {file_path}")
            except Exception as e:
                print(f"Error removing {file_path}: {e}")

def cleanup_docker():
    """Clean up Docker artifacts."""
    print("To clean Docker artifacts, run:")
    print("docker system prune -af")
    print("docker volume prune -f")

def main():
    """Main cleanup function."""
    print("Starting project cleanup...")
    cleanup_logs()
    cleanup_docker()
    print("Cleanup completed!")

if __name__ == "__main__":
    main()
