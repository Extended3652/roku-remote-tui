"""Input handling with flood protection."""
import curses
import time

class InputHandler:
    def __init__(self, state, roku):
        self.state = state
        self.roku = roku
        self._last_wheel_time = 0.0
        self._wheel_min_gap_apps = 0.02
        self._wheel_min_gap_remote = 0.15
        self._last_vol_time = 0.0
        self._vol_min_gap = 0.25
        self._redraw = None  # optional callback for forcing a mid-handler redraw

    def set_redraw(self, fn):
        self._redraw = fn

    def _send(self, args, ok_msg):
        """Run a Roku command and surface any error in the status bar."""
        result = self.roku.run(args)
        if result:
            self.state.set_message(ok_msg)
        else:
            err = getattr(self.roku, 'last_error', None) or "No response from device"
            self.state.set_message(f"Error: {err}")
    
    def handle(self, ch):
        # DEVICE SELECTOR has priority (can close other overlays)
        if self.state.devices_open:
            return self._handle_device_selector(ch)
        
        # HELP HAS TOP PRIORITY
        if self.state.help_open:
            if ch in (27, ord('?')):
                self.state.help_open = False
                self.state.set_message("Help closed")
            return None
        
        # STATS OVERLAY
        if self.state.stats_open:
            if ch in (27, ord('S'), ord('s')):
                self.state.stats_open = False
                self.state.set_message("Stats closed")
            return None
        
        # LAUNCHER
        if self.state.launcher_open:
            return self._handle_launcher(ch)
        
        # TYPING MODE
        if self.state.typing_mode:
            return self._handle_typing(ch)
        
        # FAVORITE ASSIGN MODE
        if self.state.fav_assign_mode:
            if ch == 27:
                self.state.cancel_fav_assign_mode()
                return None
            if 0 <= ch <= 255 and chr(ch) in "123456789":
                slot = int(chr(ch)) - 1
                self.state.assign_favorite(slot)
                return None
            return None
        
        # Handle mouse events
        if ch == curses.KEY_MOUSE:
            return self._handle_mouse()
        
        # GLOBAL KEYS
        
        # D/d key: Device selector
        if ch == ord('D') or ch == ord('d'):
            self.state.open_device_selector()
            return None
        
        # T key: cycle theme
        if ch == ord('T'):
            self.state.cycle_theme()
            return None
        
        # S key: toggle stats
        if ch == ord('S'):
            self.state.stats_open = not self.state.stats_open
            if self.state.stats_open:
                self.state.set_message("Stats: Press S or Esc to close")
            return None
        
        # / key: open launcher
        if 0 <= ch <= 255 and chr(ch) == "/":
            self.state.open_launcher()
            return None
        
        # F key (uppercase only): enter favorite assign mode
        if 0 <= ch <= 255 and chr(ch) == "F":
            self.state.start_fav_assign_mode()
            return None
        
        # 1-9: launch favorites
        if 0 <= ch <= 255 and chr(ch) in "123456789":
            slot = int(chr(ch)) - 1
            self.state.launch_favorite(slot)
            return None
        
        # Quit
        if ch == ord('q') or ch == ord('Q'):
            return "quit"
        
        # Help
        if ch == ord('?'):
            self.state.help_open = not self.state.help_open
            return None
        
        # Tab: toggle focus
        if ch == 9:
            self.state.focus = "apps" if self.state.focus == "remote" else "remote"
            self.state.set_message(f"Focus: {self.state.focus.upper()}")
            return None

        # h/H: Home (global - works from any focus)
        if ch == ord('h') or ch == ord('H'):
            self._send(["home"], "Home")
            return None

        # p/P: Power toggle (global)
        if ch == ord('p') or ch == ord('P'):
            self._send(["power"], "Power")
            return None

        # Apps navigation
        if self.state.focus == "apps":
            return self._handle_apps(ch)
        
        # Remote navigation
        return self._handle_remote(ch)
    
    def _handle_device_selector(self, ch):
        """Handle device selector overlay."""
        # Close on Esc or D
        if ch in (27, ord('D'), ord('d')):
            self.state.close_device_selector()
            return None
        
        # Get devices list
        devices = self.state.device_manager.get_all()
        
        # Arrow Up
        if ch == curses.KEY_UP:
            if devices and self.state.devices_sel > 0:
                self.state.devices_sel -= 1
            return None
        
        # Arrow Down
        if ch == curses.KEY_DOWN:
            if devices and self.state.devices_sel < len(devices) - 1:
                self.state.devices_sel += 1
            return None
        
        # Enter: Switch to selected device
        if ch in (10, 13, curses.KEY_ENTER):
            if devices and 0 <= self.state.devices_sel < len(devices):
                selected = devices[self.state.devices_sel]
                self.state.switch_device(selected['id'])
                # Stay in selector so user can see the change
            return None
        
        # Scan for devices on 's'
        if ch == ord('s') or ch == ord('S'):
            self.state.devices_scanning = True
            self.state.set_message("Scanning network for Roku devices...")
            if self._redraw:
                self._redraw()
            from roku_remote_tui.roku.discovery import discover_devices
            found = discover_devices()
            for device in found:
                self.state.device_manager.add_device(device)
            self.state.devices_scanning = False
            self.state.set_message(f"Found {len(found)} device(s)")
            return None
        
        return None

    def _handle_launcher(self, ch):
        if ch in (27, 9):
            self.state.close_launcher()
            return None
        if ch in (10, 13, curses.KEY_ENTER):
            self.state.launch_from_launcher()
            return None
        if ch in (curses.KEY_BACKSPACE, 127, 8):
            if self.state.launcher_query:
                self.state.launcher_query = self.state.launcher_query[:-1]
                self.state.rebuild_launcher_matches()
            return None
        if ch == curses.KEY_UP:
            if self.state.launcher_sel > 0:
                self.state.launcher_sel -= 1
            self.state.ensure_launcher_visible()
            return None
        if ch == curses.KEY_DOWN:
            if self.state.launcher_sel < len(self.state.launcher_matches) - 1:
                self.state.launcher_sel += 1
            self.state.ensure_launcher_visible()
            return None
        if 0 <= ch <= 255:
            c = chr(ch)
            if c.isprintable():
                self.state.launcher_query += c
                self.state.rebuild_launcher_matches()
                self.state.launcher_sel = 0
                self.state.launcher_scroll = 0
        return None
    
    def _handle_mouse(self):
        try:
            _, mx, my, _, bstate = curses.getmouse()
            now = time.time()
            if self.state.focus == "apps":
                if (now - self._last_wheel_time) < self._wheel_min_gap_apps:
                    return None
                if bstate & curses.BUTTON4_PRESSED:
                    if self.state.apps:
                        if self.state.apps_selected > 0:
                            self.state.apps_selected -= 1
                        else:
                            self.state.apps_selected = len(self.state.apps) - 1
                        self.state.ensure_apps_visible()
                        self._last_wheel_time = now
                    return None
                if bstate & curses.BUTTON5_PRESSED:
                    if self.state.apps:
                        if self.state.apps_selected < len(self.state.apps) - 1:
                            self.state.apps_selected += 1
                        else:
                            self.state.apps_selected = 0
                        self.state.ensure_apps_visible()
                        self._last_wheel_time = now
                    return None
            elif self.state.focus == "remote":
                if (now - self._last_wheel_time) < self._wheel_min_gap_remote:
                    return None
                if bstate & curses.BUTTON4_PRESSED:
                    self.roku.run(["nav", "up", "1"])
                    self.state.set_message("Wheel: Up")
                    self._last_wheel_time = now
                    return None
                if bstate & curses.BUTTON5_PRESSED:
                    self.roku.run(["nav", "down", "1"])
                    self.state.set_message("Wheel: Down")
                    self._last_wheel_time = now
                    return None
        except:
            pass
        return None
    
    def _handle_typing(self, ch):
        if ch == 27:
            self.state.exit_typing_mode()
            return None
        if ch in (10, 13, curses.KEY_ENTER):
            self.state.send_typed_text()
            return None
        if ch in (curses.KEY_BACKSPACE, 127, 8):
            if self.state.type_buf:
                self.state.type_buf = self.state.type_buf[:-1]
            return None
        if 0 <= ch <= 255:
            c = chr(ch)
            if c.isprintable():
                self.state.type_buf += c
        return None
    
    def _handle_apps(self, ch):
        if not self.state.apps:
            return None
        if ch == curses.KEY_UP:
            if self.state.apps_selected > 0:
                self.state.apps_selected -= 1
            else:
                self.state.apps_selected = len(self.state.apps) - 1
            self.state.ensure_apps_visible()
            return None
        if ch == curses.KEY_DOWN:
            if self.state.apps_selected < len(self.state.apps) - 1:
                self.state.apps_selected += 1
            else:
                self.state.apps_selected = 0
            self.state.ensure_apps_visible()
            return None
        if ch in (10, 13, curses.KEY_ENTER):
            self.state.launch_app()
            return None
        if ch == ord('r') or ch == ord('R'):
            self.state.load_apps(first=False)
            return None
        return None
    
    def _handle_remote(self, ch):
        if ch == ord('t') or ch == ord('T'):
            self.state.enter_typing_mode()
            return None
        if ch == curses.KEY_UP:
            self._send(["nav", "up", "1"], "Up")
            return None
        if ch == curses.KEY_DOWN:
            self._send(["nav", "down", "1"], "Down")
            return None
        if ch == curses.KEY_LEFT:
            self._send(["nav", "left", "1"], "Left")
            return None
        if ch == curses.KEY_RIGHT:
            self._send(["nav", "right", "1"], "Right")
            return None
        if ch in (10, 13, curses.KEY_ENTER):
            self._send(["ok", "1"], "OK")
            return None
        if ch in (curses.KEY_BACKSPACE, 127, 8):
            self._send(["back", "1"], "Back")
            return None
        if ch == ord('i') or ch == ord('I'):
            self._send(["info"], "Info")
            return None
        if ch == ord('r') or ch == ord('R'):
            self._send(["replay"], "Replay")
            return None
        if ch == ord(' '):
            self._send(["play"], "Play/Pause")
            return None
        if ch == ord('b') or ch == ord('B'):
            self._send(["rev", "1"], "Rewind")
            return None
        if ch == ord('f'):
            self._send(["fwd", "1"], "Fast Forward")
            return None
        if ch == ord('m') or ch == ord('M'):
            self._send(["mute"], "Mute")
            return None
        if ch == ord('=') or ch == ord('+'):
            now = time.time()
            if (now - self._last_vol_time) >= self._vol_min_gap:
                self._send(["vol", "up", "1"], "Volume Up")
                self._last_vol_time = now
            return None
        if ch == ord('-') or ch == ord('_'):
            now = time.time()
            if (now - self._last_vol_time) >= self._vol_min_gap:
                self._send(["vol", "down", "1"], "Volume Down")
                self._last_vol_time = now
            return None
        return None
