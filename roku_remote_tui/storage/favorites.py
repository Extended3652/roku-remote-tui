"""Favorites persistence."""
import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "roku_remote_tui"
FAV_FILE = CONFIG_DIR / "favorites.json"

class FavoritesManager:
    def __init__(self):
        self.slots = [None] * 9
        self.load()
    
    def load(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if not FAV_FILE.exists():
            return
        try:
            with open(FAV_FILE, 'r') as f:
                data = json.load(f)
            slots = data.get("slots", [])
            if isinstance(slots, list):
                self.slots = [None] * 9
                for i in range(min(9, len(slots))):
                    item = slots[i]
                    if isinstance(item, dict) and item.get("arg"):
                        self.slots[i] = {"label": item.get("label") or item.get("arg"), "arg": item["arg"]}
        except:
            pass
    
    def save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(FAV_FILE, 'w') as f:
                json.dump({"slots": self.slots}, f, indent=2)
            return True
        except:
            return False
    
    def get_slot(self, index):
        if 0 <= index < 9:
            return self.slots[index]
        return None
    
    def set_slot(self, index, label, arg):
        if 0 <= index < 9:
            self.slots[index] = {"label": label, "arg": arg}
            return self.save()
        return False
