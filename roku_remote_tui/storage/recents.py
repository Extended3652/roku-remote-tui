"""Recent apps tracking."""
import json
from pathlib import Path
from datetime import datetime

CACHE_DIR = Path.home() / ".cache" / "roku_remote_tui"
RECENT_FILE = CACHE_DIR / "recent.json"
MAX_RECENT = 10

class RecentsManager:
    def __init__(self):
        self.recents = []
        self.load()
    
    def load(self):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        if not RECENT_FILE.exists():
            return
        try:
            with open(RECENT_FILE, 'r') as f:
                data = json.load(f)
            recents = data.get("recents", [])
            if isinstance(recents, list):
                self.recents = recents[:MAX_RECENT]
        except:
            pass
    
    def save(self):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(RECENT_FILE, 'w') as f:
                json.dump({"recents": self.recents}, f, indent=2)
            return True
        except:
            return False
    
    def add(self, label, arg):
        self.recents = [r for r in self.recents if r.get("arg") != arg]
        self.recents.insert(0, {"label": label, "arg": arg, "timestamp": datetime.now().isoformat()})
        self.recents = self.recents[:MAX_RECENT]
        return self.save()
    
    def get_all(self):
        return self.recents
