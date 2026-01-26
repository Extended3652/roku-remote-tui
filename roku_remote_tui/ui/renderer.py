"""UI rendering."""
import curses
import time

class Renderer:
    def __init__(self, stdscr, state):
        self.stdscr = stdscr
        self.state = state
    
    def init_colors(self):
        if not curses.has_colors():
            return
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        curses.init_pair(4, curses.COLOR_RED, -1)
        curses.init_pair(5, curses.COLOR_WHITE, -1)
        curses.init_pair(6, curses.COLOR_MAGENTA, -1)
    
    def draw(self):
        self.stdscr.erase()
        maxy, maxx = self.stdscr.getmaxyx()
        title = f"Roku Remote TUI v2.1 [{self.state.theme.get_theme_name()}]"
        self._addstr(0, 2, title, self.state.theme.get_color("title"), curses.A_BOLD)
        mode = "TYPING" if self.state.typing_mode else ("APPS" if self.state.focus == "apps" else "NAV")
        online = "ONLINE" if self.state.online else "OFFLINE" if self.state.online is False else "UNKNOWN"
        status = f"[ {mode} ]  [ {online} ]"
        self._addstr(0, maxx - len(status) - 2, status, self.state.theme.get_color("status"), curses.A_BOLD)
        top = 2
        bottom_reserved = 3
        main_h = max(10, maxy - top - bottom_reserved)
        avail_w = max(10, maxx - 2)
        left_w = min(30, max(24, avail_w // 4))
        mid_w = min(44, max(34, avail_w // 3))
        right_w = avail_w - left_w - mid_w - 4
        if right_w < 26:
            need = 26 - right_w
            shrink_mid = min(need, max(0, mid_w - 28))
            mid_w -= shrink_mid
            need -= shrink_mid
            shrink_left = min(need, max(0, left_w - 22))
            left_w -= shrink_left
            right_w = avail_w - left_w - mid_w - 4
        right_w = max(26, right_w)
        self._draw_quick_keys_panel(top, 1, main_h, left_w)
        self._draw_remote_panel(top, left_w + 2, main_h, mid_w)
        self._draw_apps_panel(top, left_w + mid_w + 3, main_h, right_w)
        self._draw_bottom(maxy, maxx)
        self._draw_launcher_overlay(maxy, maxx)
        self._draw_help_overlay(maxy, maxx)
        self._draw_stats_overlay(maxy, maxx)
    
    def _draw_quick_keys_panel(self, y, x, h, w):
        border_color = self.state.theme.get_color("border")
        self._draw_box(y, x, h, w, "Quick Keys", border_color, curses.A_DIM)
        lines = [
            ("/: launcher", 5, 0), ("Tab: switch focus", 5, 0), ("q: quit", 5, 0), ("?: help", 5, 0),
            ("Shift+T: theme", 5, 0), ("Shift+S: stats", 5, 0), ("", 5, 0), ("Remote:", 3, curses.A_BOLD),
            ("Arrows: navigate", 5, 0), ("Enter: OK", 5, 0), ("Backspace: Back", 5, 0), ("h: Home", 5, 0),
            ("Space: Play/Pause", 5, 0), ("m: Mute", 5, 0), ("- / =: Volume", 5, 0), ("", 5, 0),
            ("Apps:", 3, curses.A_BOLD), ("↑↓: select", 5, 0), ("Enter: launch", 5, 0), ("r: refresh", 5, 0)
        ]
        qy = y + 2
        qx = x + 3
        for text, color, attr in lines:
            if qy >= y + h - 1:
                break
            self._addstr(qy, qx, text[:max(0, w - 4)], color, attr)
            qy += 1
    
    def _draw_remote_panel(self, y, x, h, w):
        remote_active = (self.state.focus == "remote")
        border_color = self.state.theme.get_color("border_active") if remote_active else self.state.theme.get_color("border")
        border_attr = 0 if remote_active else curses.A_DIM
        title_attr = (curses.A_BOLD | curses.A_REVERSE) if remote_active else 0
        self._draw_box(y, x, h, w, "Remote", border_color, border_attr | title_attr)
        art = [
            "┌─────────────────────────┐", "│       Roku Remote       │", "├─────────────────────────┤",
            "│  [h] Home               │", "│                         │", "│         ┌─────┐         │",
            "│         │  ↑  │         │", "│    ┌────┘     └────┐    │", "│    │  ←   O·K   →  │    │",
            "│    └────┐     ┌────┘    │", "│         │  ↓  │         │", "│         └─────┘         │",
            "│                         │", "│   Backspace = Back      │", "│       Enter = OK        │",
            "│                         │", "│  [r] Replay   [i] Info  │", "│  [b] Rev      [f] Fwd   │",
            "│  [Space] Play/Pause     │", "│                         │", "│  Vol: - down, =/+ up    │",
            "│  Mute: m                │", "│                         │", "│  Focus: Tab             │",
            "└─────────────────────────┘"
        ]
        art_color = 2 if remote_active else 5
        art_attr = curses.A_BOLD if remote_active else 0
        inner_h = max(1, h - 2)
        inner_w = max(1, w - 4)
        art_h = len(art)
        art_w = max(len(line) for line in art) if art else 0
        ry = y + 1 + max(0, (inner_h - art_h) // 2)
        rx = x + 2 + max(0, (inner_w - art_w) // 2)
        for i, line in enumerate(art):
            if ry + i >= y + h - 1:
                break
            self._addstr(ry + i, rx, line[:max(0, inner_w)], art_color, art_attr)
    
    def _draw_apps_panel(self, y, x, h, w):
        apps_active = (self.state.focus == "apps")
        border_color = self.state.theme.get_color("border_active") if apps_active else self.state.theme.get_color("border")
        border_attr = 0 if apps_active else curses.A_DIM
        title_attr = (curses.A_BOLD | curses.A_REVERSE) if apps_active else 0
        self._draw_box(y, x, h, w, "Apps", border_color, border_attr | title_attr)
        inner_y = y + 1
        inner_x = x + 2
        inner_w = w - 4
        if not self.state.apps:
            self._addstr(inner_y, inner_x, "Loading apps...", 3)
            return
        total = len(self.state.apps)
        self._addstr(inner_y, inner_x, f"Total: {total} apps/inputs", 3, curses.A_BOLD)
        inner_y += 2
        list_height = h - 5
        self.state._apps_list_h = list_height
        visible = h - 5
        start = self.state.apps_scroll
        end = min(len(self.state.apps), start + visible)
        row_y = inner_y
        for i in range(start, end):
            if row_y >= y + h - 2:
                break
            app = self.state.apps[i]
            name = app.get("display") or app.get("name") or "?"
            typ = app.get("type")
            suffix = " (input)" if typ == "tvin" else ""
            is_selected = (i == self.state.apps_selected)
            fav_marker = ""
            app_arg = app.get("arg") or ""
            for fav_idx in range(9):
                fav = self.state.favorites.get_slot(fav_idx)
                if fav and fav.get("arg") == app_arg:
                    fav_marker = f" [F{fav_idx + 1}]"
                    break
            if is_selected:
                text = f"> {name}{suffix}{fav_marker}"
                self._addstr(row_y, inner_x, text[:inner_w], self.state.theme.get_color("selected"), curses.A_REVERSE | curses.A_BOLD)
            else:
                text = f"  {name}{suffix}{fav_marker}"
                color = self.state.theme.get_color("favorite") if fav_marker else self.state.theme.get_color("text")
                self._addstr(row_y, inner_x, text[:inner_w], color)
            row_y += 1
        footer = "↑↓: select  Enter: launch  r: refresh  Tab: focus"
        self._addstr(y + h - 1, x + 2, footer[:w-4], 3)
    
    def _draw_bottom(self, maxy, maxx):
        if self.state.typing_mode:
            self._draw_box(maxy - 3, 1, 3, maxx - 2, "Typing", 6, curses.A_BOLD)
            buf = self.state.type_buf
            if len(buf) > maxx - 8:
                buf = "..." + buf[-(maxx - 11):]
            self._addstr(maxy - 2, 3, buf, 3, curses.A_BOLD)
            self._addstr(maxy - 1, 2, "Esc exits typing. Enter sends.", 3)
        else:
            hint = "Tip: Press ? for help. / for launcher. Tab to switch focus. q to quit"
            self._addstr(maxy - 2, 2, hint[:maxx-4], 3)
            msg = self.state.get_visible_message()
            status_line = f"Status: {msg}" if msg else "Status: Ready"
            self._addstr(maxy - 1, 2, status_line[:maxx-4], 5)
    
    def _draw_launcher_overlay(self, maxy, maxx):
        if not self.state.launcher_open:
            return
        h = 4 + self.state.launcher_visible + 3
        w = min(maxx - 4, 70)
        y = max(1, (maxy - h) // 2)
        x = max(2, (maxx - w) // 2)
        for yy in range(y, min(y + h, maxy)):
            try:
                self._addstr(yy, x, " " * min(w, maxx - x - 1), 0, 0)
            except:
                pass
        self._draw_box(y, x, h, w, "Launch", 6, curses.A_BOLD)
        q_disp = self.state.launcher_query
        if len(q_disp) > w - 18:
            q_disp = "..." + q_disp[-(w - 21):]
        count = len(self.state.launcher_matches)
        self._addstr(y + 1, x + 2, f"Search: {q_disp}  ({count} matches)", 3, curses.A_BOLD)
        sel_line = ""
        if self.state.launcher_matches:
            item = self.state.launcher_matches[self.state.launcher_sel]
            sel_line = self.state.launcher_item_display(item)
        if sel_line:
            self._addstr(y + 2, x + 2, ("Selected: " + sel_line)[:max(0, w - 4)], 5, 0)
        start = self.state.launcher_scroll
        end = min(len(self.state.launcher_matches), start + self.state.launcher_visible)
        row_y = y + 3
        if not self.state.launcher_matches:
            self._addstr(row_y, x + 2, "No matches", 4, curses.A_BOLD)
        else:
            for mi in range(start, end):
                item = self.state.launcher_matches[mi]
                line = self.state.launcher_item_display(item)
                line = line[:max(0, w - 6)]
                selected = (mi == self.state.launcher_sel)
                if selected:
                    self._addstr(row_y, x + 2, f"> {line}", 6, curses.A_BOLD)
                else:
                    self._addstr(row_y, x + 2, f"  {line}", 5, 0)
                row_y += 1
        footer = "Enter: launch  Esc/Tab: close  ↑↓: select  Type: search"
        self._addstr(y + h - 2, x + 2, footer[:w-4], 3, 0)
    
    def _draw_help_overlay(self, maxy, maxx):
        if not self.state.help_open:
            return
        help_lines = [
            ("NAVIGATION", 6, curses.A_BOLD), ("  Tab         Switch focus (Remote/Apps)", 5, 0),
            ("  ↑↓←→        Navigate", 5, 0), ("  Enter       OK / Launch", 5, 0), ("  Backspace   Back", 5, 0),
            ("", 5, 0), ("REMOTE CONTROL", 6, curses.A_BOLD), ("  h           Home", 5, 0),
            ("  Space       Play/Pause", 5, 0), ("  r           Replay", 5, 0), ("  i           Info", 5, 0),
            ("  b           Rewind", 5, 0), ("  m           Mute", 5, 0), ("  - / =       Volume down/up", 5, 0),
            ("", 5, 0), ("FEATURES", 6, curses.A_BOLD), ("  /           Launcher", 3, 0),
            ("  t           Typing mode", 3, 0), ("  F then 1-9  Set favorite", 3, 0),
            ("  1-9         Launch favorite", 3, 0), ("  r           Refresh apps", 5, 0),
            ("", 5, 0), ("GENERAL", 6, curses.A_BOLD), ("  ?           Help", 5, 0),
            ("  Shift+S     Statistics", 5, 0), ("  Shift+T     Theme", 5, 0), ("  q           Quit", 5, 0)
        ]
        h = min(len(help_lines) + 4, maxy - 4)
        w = min(75, maxx - 4)
        y = max(1, (maxy - h) // 2)
        x = max(2, (maxx - w) // 2)
        for yy in range(y, min(y + h, maxy)):
            try:
                self._addstr(yy, x, " " * min(w, maxx - x - 1), 0, 0)
            except:
                pass
        self._draw_box(y, x, h, w, "Help", 6, curses.A_BOLD)
        row_y = y + 1
        for line_text, color, attr in help_lines:
            if row_y >= y + h - 2:
                break
            self._addstr(row_y, x + 2, line_text[:w-4], color, attr)
            row_y += 1
        self._addstr(y + h - 1, x + 2, "Press ? or Esc to close", 3, 0)
    
    def _draw_stats_overlay(self, maxy, maxx):
        if not self.state.stats_open:
            return
        h = min(18, maxy - 4)
        w = min(60, maxx - 4)
        y = max(1, (maxy - h) // 2)
        x = max(2, (maxx - w) // 2)
        for yy in range(y, min(y + h, maxy)):
            try:
                self._addstr(yy, x, " " * min(w, maxx - x - 1), 0, 0)
            except:
                pass
        self._draw_box(y, x, h, w, "Statistics", 6, curses.A_BOLD)
        total = self.state.stats.total_launches
        self._addstr(y + 1, x + 2, f"Total Launches: {total}", 3, curses.A_BOLD)
        self._addstr(y + 3, x + 2, "Most Used Apps:", 3, curses.A_BOLD)
        top_apps = self.state.stats.get_top_apps(10)
        row_y = y + 4
        if not top_apps:
            self._addstr(row_y, x + 4, "No statistics yet", 5, 0)
        else:
            for i, (arg, data) in enumerate(top_apps, 1):
                if row_y >= y + h - 2:
                    break
                label = data.get("label", arg)
                count = data.get("count", 0)
                max_label_len = w - 15
                if len(label) > max_label_len:
                    label = label[:max_label_len-3] + "..."
                line = f"{i:2}. {label:<{max_label_len}} {count:>4}×"
                self._addstr(row_y, x + 4, line[:w-6], 5, 0)
                row_y += 1
        self._addstr(y + h - 1, x + 2, "Press S or Esc to close", 3, 0)
    
    def _draw_box(self, y, x, h, w, title="", color=0, attr=0):
        maxy, maxx = self.stdscr.getmaxyx()
        if h < 2 or w < 2 or y >= maxy or x >= maxx:
            return
        h = min(h, maxy - y)
        w = min(w, maxx - x)
        if h < 2 or w < 2:
            return
        box_attr = (curses.color_pair(color) if color else 0) | attr
        try:
            self.stdscr.addch(y, x, "┌", box_attr)
            self.stdscr.addch(y, x + w - 1, "┐", box_attr)
            self.stdscr.addch(y + h - 1, x, "└", box_attr)
            self.stdscr.addch(y + h - 1, x + w - 1, "┘", box_attr)
            for i in range(1, w - 1):
                self.stdscr.addch(y, x + i, "─", box_attr)
                self.stdscr.addch(y + h - 1, x + i, "─", box_attr)
            for j in range(1, h - 1):
                self.stdscr.addch(y + j, x, "│", box_attr)
                self.stdscr.addch(y + j, x + w - 1, "│", box_attr)
        except curses.error:
            pass
        if title:
            t = f" {title} "
            tx = x + 2
            if tx + len(t) < x + w - 2:
                self._addstr(y, tx, t, color, attr)
    
    def _addstr(self, y, x, text, color=0, attr=0):
        maxy, maxx = self.stdscr.getmaxyx()
        if y < 0 or y >= maxy or x < 0 or x >= maxx:
            return
        max_len = max(0, maxx - x - 1)
        text = text[:max_len]
        if not text:
            return
        try:
            if color:
                self.stdscr.addnstr(y, x, text, len(text), curses.color_pair(color) | attr)
            else:
                self.stdscr.addnstr(y, x, text, len(text), attr)
        except curses.error:
            pass
