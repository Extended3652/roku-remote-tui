"""Usage statistics tracking."""
import json
from pathlib import Path
from datetime import datetime

CACHE_DIR = Path.home() / ".cache" / "roku_remote_tui"
STATS_FILE = CACHE_DIR / "stats.json"

class StatsManager:
    def __init__(self):
        self.stats = {}
        self.total_launches = 0
        self.load()
    
    def load(self):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        if not STATS_FILE.exists():
            return
        try:
            with open(STATS_FILE, 'r') as f:
                data = json.load(f)
            self.stats = data.get("stats", {})
            self.total_launches = data.get("total_launches", 0)
        except:
            pass
    
    def save(self):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(STATS_FILE, 'w') as f:
                json.dump({"stats": self.stats, "total_launches": self.total_launches}, f, indent=2)
            return True
        except:
            return False
    
    def record_launch(self, label, arg):
        if arg not in self.stats:
            self.stats[arg] = {"count": 0, "label": label, "first_launch": datetime.now().isoformat()}
        self.stats[arg]["count"] += 1
        self.stats[arg]["last_launch"] = datetime.now().isoformat()
        self.stats[arg]["label"] = label
        self.total_launches += 1
        return self.save()
    
    def get_top_apps(self, n=5):
        sorted_apps = sorted(self.stats.items(), key=lambda x: x[1]["count"], reverse=True)
        return sorted_apps[:n]
