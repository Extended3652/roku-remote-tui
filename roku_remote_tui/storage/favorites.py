"""Favorites persistence, stored per device."""
import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "roku_remote_tui"
FAV_FILE = CONFIG_DIR / "favorites.json"

class FavoritesManager:
    def __init__(self):
        self.slots = [None] * 9
        self._device_id = "default"
        self._by_device = {}
        self._load_file()

    # ------------------------------------------------------------------
    # File I/O
    # ------------------------------------------------------------------

    def _load_file(self):
        """Load the entire favorites file into self._by_device."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if not FAV_FILE.exists():
            return
        try:
            with open(FAV_FILE, 'r') as f:
                data = json.load(f)
        except Exception:
            return

        if "by_device" in data:
            # Current format
            self._by_device = data["by_device"]
        elif "slots" in data:
            # Legacy format (single global set) — migrate to "default" device
            self._by_device = {"default": {"slots": data["slots"]}}
        # Load slots for whichever device is currently active
        self._apply_device_slots()

    def _apply_device_slots(self):
        """Populate self.slots from the stored data for self._device_id."""
        stored = self._by_device.get(self._device_id, {})
        raw = stored.get("slots", [])
        self.slots = [None] * 9
        for i in range(min(9, len(raw))):
            item = raw[i]
            if isinstance(item, dict) and item.get("arg"):
                self.slots[i] = {"label": item.get("label") or item.get("arg"), "arg": item["arg"]}

    def _flush_current(self):
        """Persist current slots into the in-memory dict for the active device."""
        self._by_device[self._device_id] = {"slots": self.slots}

    def save(self):
        self._flush_current()
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(FAV_FILE, 'w') as f:
                json.dump({"by_device": self._by_device}, f, indent=2)
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Device switching
    # ------------------------------------------------------------------

    def switch_device(self, device_id):
        """Save current device's favorites then load the new device's."""
        self._flush_current()
        self._device_id = device_id or "default"
        self._apply_device_slots()

    # ------------------------------------------------------------------
    # Slot access
    # ------------------------------------------------------------------

    def get_slot(self, index):
        if 0 <= index < 9:
            return self.slots[index]
        return None

    def set_slot(self, index, label, arg):
        if 0 <= index < 9:
            self.slots[index] = {"label": label, "arg": arg}
            return self.save()
        return False
