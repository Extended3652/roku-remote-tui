#!/usr/bin/env python3
"""Run the Roku Remote TUI."""
import sys
import os

if not sys.stdin.isatty():
    print("Error: This application requires a TTY terminal", file=sys.stderr)
    sys.exit(1)

import curses
from roku_remote_tui.app import main

if __name__ == "__main__":
    main()
