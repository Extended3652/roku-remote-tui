"""Device configuration and management."""
import json
from pathlib import Path
from datetime import datetime

CONFIG_DIR = Path.home() / ".config" / "roku_remote_tui"
DEVICES_FILE = CONFIG_DIR / "devices.json"

class DeviceManager:
    def __init__(self):
        self.devices = {}
        self.active_device_id = None
        self.load()
    
    def load(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if not DEVICES_FILE.exists():
            return
        try:
            with open(DEVICES_FILE, 'r') as f:
                data = json.load(f)
            self.devices = data.get("devices", {})
            self.active_device_id = data.get("active_device_id")
        except:
            pass
    
    def save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(DEVICES_FILE, 'w') as f:
                json.dump({"devices": self.devices, "active_device_id": self.active_device_id}, f, indent=2)
            return True
        except:
            return False
    
    def add_device(self, device_info):
        device_id = device_info.get('serial') or f"ip_{device_info['ip'].replace('.', '_')}"
        self.devices[device_id] = {
            'name': device_info['name'],
            'ip': device_info['ip'],
            'model': device_info.get('model', 'Unknown'),
            'serial': device_info.get('serial'),
            'added_at': datetime.now().isoformat()
        }
        if self.active_device_id is None:
            self.active_device_id = device_id
        self.save()
        return device_id
    
    def set_active(self, device_id):
        if device_id in self.devices:
            self.active_device_id = device_id
            self.save()
            return True
        return False
    
    def get_active(self):
        if self.active_device_id and self.active_device_id in self.devices:
            device = self.devices[self.active_device_id].copy()
            device['id'] = self.active_device_id
            return device
        return None
    
    def get_all(self):
        return [{**info, 'id': device_id, 'active': device_id == self.active_device_id} for device_id, info in self.devices.items()]
