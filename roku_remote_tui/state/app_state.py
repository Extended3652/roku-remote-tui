"""Application state management."""
import time
from pathlib import Path
from roku_remote_tui.storage.favorites import FavoritesManager
from roku_remote_tui.storage.recents import RecentsManager
from roku_remote_tui.storage.stats import StatsManager
from roku_remote_tui.storage.devices import DeviceManager
from roku_remote_tui.utils.fuzzy import fuzzy_score
from roku_remote_tui.config.themes import ThemeManager

class AppState:
    def __init__(self, roku_cli):
        self.roku = roku_cli

        # Device management
        self.device_manager = DeviceManager()
        self.favorites = FavoritesManager()
        self._setup_device()
        
        self.focus = "remote"
        self.typing_mode = False
        self.type_buf = ""
        self.theme = ThemeManager()
        self.message = "Ready"
        self.message_time = time.time()
        self.apps = []
        self.apps_loaded = False
        self.apps_selected = 0
        self.apps_scroll = 0
        self._apps_list_h = 10
        self.recents = RecentsManager()
        self.stats = StatsManager()
        self.fav_assign_mode = False
        self.fav_assign_until = 0.0
        self.launcher_open = False
        self.launcher_query = ""
        self.launcher_matches = []
        self.launcher_sel = 0
        self.launcher_scroll = 0
        self.launcher_visible = 10
        self.help_open = False
        self.stats_open = False
        self.devices_open = False
        self.devices_sel = 0
        self.devices_scanning = False
        self.ok_hold_active = False
        self.ok_hold_end = 0.0
        self.last_vol_sent = 0.0
        self.online = None
    
    def _setup_device(self):
        """Setup roku CLI with active device."""
        active = self.device_manager.get_active()
        if active:
            self.roku.set_device(active['ip'])
            self.favorites.switch_device(active['id'])
            self.set_message(f"Device: {active['name']}")
        else:
            self.set_message("No device configured - use Ctrl+D to add")
    
    def get_current_device_name(self):
        """Get name of current device."""
        active = self.device_manager.get_active()
        return active['name'] if active else "No Device"
    
    def switch_device(self, device_id):
        """Switch to a different device, reloading apps and favorites."""
        if self.device_manager.set_active(device_id):
            active = self.device_manager.get_active()
            self.roku.set_device(active['ip'])
            self.favorites.switch_device(active['id'])
            self.set_message(f"Switched to: {active['name']}")
            self.load_apps(first=True)
            return True
        return False
    
    def open_device_selector(self):
        """Open device selector overlay."""
        devices = self.device_manager.get_all()
        self.devices_sel = 0
        # Set selection to current active device
        for i, d in enumerate(devices):
            if d['active']:
                self.devices_sel = i
                break
        self.devices_open = True
    
    def close_device_selector(self):
        """Close device selector overlay."""
        self.devices_open = False
    
    def cycle_theme(self):
        theme_name = self.theme.next_theme()
        self.set_message(f"Theme: {theme_name}")
    
    def set_message(self, text):
        self.message = text
        self.message_time = time.time()
    
    def get_visible_message(self):
        if (time.time() - self.message_time) < 6.0:
            return self.message
        return ""
    
    def open_launcher(self):
        if not self.apps:
            self.set_message("No apps loaded")
            return
        self.launcher_open = True
        self.launcher_query = ""
        self.rebuild_launcher_matches()
        self.launcher_sel = 0
        self.launcher_scroll = 0
        self.set_message("Launcher: type to search, Enter to launch, Esc to close")
    
    def close_launcher(self):
        self.launcher_open = False
        self.launcher_query = ""
        self.launcher_matches = []
        self.launcher_sel = 0
        self.launcher_scroll = 0
        self.set_message("Launcher closed")
    
    def rebuild_launcher_matches(self):
        q = self.launcher_query.strip()
        if not q:
            self.launcher_matches = []
            seen = set()
            for recent in self.recents.get_all()[:5]:
                arg = recent.get("arg")
                if arg and arg not in seen:
                    seen.add(arg)
                    self.launcher_matches.append({"kind": "recent", "label": recent.get("label"), "arg": arg})
            for i in range(9):
                fav = self.favorites.get_slot(i)
                if fav:
                    arg = fav.get("arg")
                    if arg and arg not in seen:
                        seen.add(arg)
                        self.launcher_matches.append({"kind": "fav", "slot": i + 1, "label": fav.get("label"), "arg": arg})
            for i, app in enumerate(self.apps):
                arg = app.get("arg")
                if arg and arg not in seen:
                    seen.add(arg)
                    self.launcher_matches.append({"kind": "app", "index": i})
        else:
            scored = []
            for i, app in enumerate(self.apps):
                text = f"{app.get('display', '')} {app.get('name', '')} {app.get('arg', '')}"
                score = fuzzy_score(q, text)
                if score > 0:
                    scored.append((i, score))
            scored.sort(key=lambda x: -x[1])
            self.launcher_matches = [{"kind": "app", "index": i} for i, _ in scored]
        if self.launcher_sel >= len(self.launcher_matches):
            self.launcher_sel = max(0, len(self.launcher_matches) - 1)
    
    def ensure_launcher_visible(self):
        vis = self.launcher_visible
        if self.launcher_sel < self.launcher_scroll:
            self.launcher_scroll = self.launcher_sel
        if self.launcher_sel >= self.launcher_scroll + vis:
            self.launcher_scroll = self.launcher_sel - vis + 1
        max_scroll = max(0, len(self.launcher_matches) - vis)
        self.launcher_scroll = max(0, min(self.launcher_scroll, max_scroll))
    
    def launch_from_launcher(self):
        if not self.launcher_matches:
            self.set_message("No matches to launch")
            return
        item = self.launcher_matches[self.launcher_sel]
        if item["kind"] in ("fav", "recent"):
            arg = item.get("arg")
            label = item.get("label")
        else:
            idx = item.get("index")
            if idx is None or idx < 0 or idx >= len(self.apps):
                self.set_message("Invalid app")
                return
            app = self.apps[idx]
            arg = app.get("arg") or app.get("name")
            label = app.get("name") or app.get("display") or arg
        if not arg:
            self.set_message("Invalid launch argument")
            return
        self.recents.add(label, arg)
        self.stats.record_launch(label, arg)
        result = self.roku.run(["launch", arg])
        if result is not None or result is False:
            self.set_message(f"Launching: {label}")
            self.close_launcher()
        else:
            self.set_message(f"Failed to launch: {label}")
    
    def launcher_item_display(self, item):
        if item["kind"] == "fav":
            return f"{item.get('label', 'Favorite')}  [F{item.get('slot')}]"
        elif item["kind"] == "recent":
            return f"{item.get('label', 'Recent')}  [Recent]"
        else:
            idx = item.get("index")
            if idx is None or idx < 0 or idx >= len(self.apps):
                return "<?>"
            app = self.apps[idx]
            display = app.get("display") or app.get("name") or "?"
            typ = app.get("type")
            return f"{display}{' (input)' if typ == 'tvin' else ''}"
    
    def enter_typing_mode(self):
        self.typing_mode = True
        self.type_buf = ""
        self.set_message("Typing mode: Enter sends, Esc exits")
    
    def exit_typing_mode(self):
        self.typing_mode = False
        self.type_buf = ""
        self.set_message("Typing mode exited")
    
    def send_typed_text(self):
        if not self.type_buf:
            self.set_message("Nothing to send")
            self.exit_typing_mode()
            return
        preview = self.type_buf[:40] + ("..." if len(self.type_buf) > 40 else "")
        result = self.roku.run(["type", self.type_buf])
        if result is not None or result is False:
            self.set_message(f"Sent: {preview}")
        else:
            self.set_message("Failed to send text")
        self.typing_mode = False
        self.type_buf = ""
    
    def start_fav_assign_mode(self):
        self.fav_assign_mode = True
        self.fav_assign_until = time.time() + 4.0
        self.set_message("Set favorite: press 1-9 to assign current app (Esc cancels)")
    
    def cancel_fav_assign_mode(self):
        self.fav_assign_mode = False
        self.fav_assign_until = 0.0
        self.set_message("Favorite assignment cancelled")
    
    def tick_fav_assign_mode(self):
        if self.fav_assign_mode and time.time() > self.fav_assign_until:
            self.fav_assign_mode = False
            self.fav_assign_until = 0.0
            self.set_message("Favorite assignment timed out")
    
    def assign_favorite(self, slot):
        if not self.apps or self.apps_selected < 0 or self.apps_selected >= len(self.apps):
            self.set_message("No valid app selected")
            return False
        app = self.apps[self.apps_selected]
        arg = app.get("arg") or app.get("name")
        label = app.get("display") or app.get("name") or arg
        if not arg:
            self.set_message("Selected app has no launch argument")
            return False
        if self.favorites.set_slot(slot, label, arg):
            self.set_message(f"Saved favorite {slot + 1}: {label}")
            self.fav_assign_mode = False
            return True
        else:
            self.set_message("Failed to save favorite")
            return False
    
    def launch_favorite(self, slot):
        fav = self.favorites.get_slot(slot)
        if not fav:
            self.set_message(f"Favorite {slot + 1} is empty. Press F then {slot + 1} to set.")
            return False
        label = fav.get("label") or fav.get("arg") or "Favorite"
        arg = fav.get("arg") or ""
        if not arg:
            self.set_message("Favorite has no launch argument")
            return False
        self.recents.add(label, arg)
        self.stats.record_launch(label, arg)
        result = self.roku.run(["launch", arg])
        if result is not None or result is False:
            self.set_message(f"Launching favorite {slot + 1}: {label}")
            return True
        else:
            self.set_message(f"Failed to launch favorite: {label}")
            return False
    
    def ensure_apps_visible(self):
        if not self.apps:
            self.apps_scroll = 0
            return
        visible = max(1, self._apps_list_h)
        sel = self.apps_selected
        if sel < self.apps_scroll:
            self.apps_scroll = sel
        if sel >= self.apps_scroll + visible:
            self.apps_scroll = sel - visible + 1
        max_scroll = max(0, len(self.apps) - visible)
        self.apps_scroll = max(0, min(self.apps_scroll, max_scroll))
    
    def load_apps(self, first=False):
        try:
            import json
            result = self.roku.run(["apps", "--json"], capture=True)
            if result and result.returncode == 0:
                data = json.loads(result.stdout)
                if isinstance(data, dict):
                    apps = data.get("apps") or data.get("rows") or []
                elif isinstance(data, list):
                    apps = data
                else:
                    apps = []
                processed = []
                for r in apps:
                    name = r.get("name") or r.get("app_name") or ""
                    arg = r.get("arg") or r.get("roku_arg") or ""
                    typ = r.get("type") or ""
                    if not arg:
                        arg = name
                    processed.append({"name": name, "arg": arg, "type": typ, "display": name or arg})
                inputs = [a for a in processed if a["type"] == "tvin"]
                apps_only = [a for a in processed if a["type"] != "tvin"]
                self.apps = inputs + apps_only
                self.apps_loaded = True
                if self.apps_selected >= len(self.apps):
                    self.apps_selected = max(0, len(self.apps) - 1)
                self.ensure_apps_visible()
                self.set_message(f"{'Loaded' if first else 'Refreshed'} {len(self.apps)} apps")
                self.online = True
            else:
                self.apps = []
                self.apps_loaded = False
                err = getattr(self.roku, 'last_error', None) or "no response"
                self.set_message(f"Failed to load apps: {err}")
                self.online = False
        except Exception as e:
            self.apps = []
            self.apps_loaded = False
            self.set_message(f"Error loading apps: {e}")
            self.online = False
    
    def launch_app(self, index=None):
        if not self.apps:
            self.set_message("No apps to launch")
            return
        if index is None:
            index = self.apps_selected
        if 0 <= index < len(self.apps):
            app = self.apps[index]
            arg = app.get("arg") or app.get("name")
            label = app.get("name") or arg
            self.recents.add(label, arg)
            self.stats.record_launch(label, arg)
            result = self.roku.run(["launch", arg])
            if result is not None or result is False:
                self.set_message(f"Launching: {label}")
            else:
                self.set_message(f"Failed to launch: {label}")
    
    def tick(self):
        if self.ok_hold_active and time.time() >= self.ok_hold_end:
            self.roku.run(["keyup", "select"])
            self.ok_hold_active = False
            self.set_message("OK released")
        self.tick_fav_assign_mode()
    
    def cleanup(self):
        if self.ok_hold_active:
            self.roku.run(["keyup", "select"])
