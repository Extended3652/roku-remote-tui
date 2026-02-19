#!/usr/bin/env python3
"""Roku Remote TUI - Main Application"""
import curses
import sys
from roku_remote_tui.ui.renderer import Renderer
from roku_remote_tui.ui.input_handler import InputHandler
from roku_remote_tui.state.app_state import AppState
from roku_remote_tui.roku.cli import RokuCLI

class RokuRemoteTUI:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.running = True
        self.roku = RokuCLI()
        self.state = AppState(self.roku)
        self.renderer = Renderer(stdscr, self.state)
        self.input_handler = InputHandler(self.state, self.roku)
        self._setup_curses()
        self.input_handler.set_redraw(self._force_redraw)
        self.state.load_apps(first=True)
    
    def _setup_curses(self):
        try:
            curses.curs_set(0)
        except:
            pass
        self.stdscr.keypad(True)
        self.stdscr.timeout(50)
        try:
            curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
            curses.mouseinterval(0)
        except:
            pass
        self.renderer.init_colors()
    
    def _force_redraw(self):
        self.renderer.draw()
        try:
            self.stdscr.refresh()
        except curses.error:
            pass

    def run(self):
        try:
            while self.running:
                self.state.tick()
                self.renderer.draw()
                try:
                    self.stdscr.refresh()
                except curses.error:
                    pass
                ch = self.stdscr.getch()
                if ch == -1:
                    continue
                if ch == curses.KEY_RESIZE:
                    continue
                result = self.input_handler.handle(ch)
                if result == "quit":
                    self.running = False
        finally:
            self.state.cleanup()

def main():
    def _curses_main(stdscr):
        app = RokuRemoteTUI(stdscr)
        app.run()
    curses.wrapper(_curses_main)

if __name__ == "__main__":
    main()
