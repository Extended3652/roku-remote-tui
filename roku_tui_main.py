#!/usr/bin/env python3
"""Roku Remote TUI - Main Launcher"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if not sys.stdin.isatty():
    print("Error: This application requires a TTY terminal", file=sys.stderr)
    sys.exit(1)

from roku_remote_tui.app import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
