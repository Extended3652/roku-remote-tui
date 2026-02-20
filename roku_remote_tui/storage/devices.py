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
            self._dedup_by_ip()
        except:
            pass

    def _dedup_by_ip(self):
        """Remove duplicate entries for the same IP.

        When a rescan creates a serial-keyed entry for a device that was
        already stored under an ip_X_X_X_X key, we end up with two entries
        pointing at the same physical device.  Favorites are always stored
        under the *original* (ip_-prefixed) key, so that is the one we keep.
        If active_device_id pointed at the dropped duplicate, we re-point it
        at the retained entry so switching and favorites both work.
        """
        seen = {}       # ip -> device_id we're keeping
        to_drop = []
        for did, info in list(self.devices.items()):
            ip = info.get('ip')
            if not ip:
                continue
            if ip not in seen:
                seen[ip] = did
            else:
                existing_id = seen[ip]
                # Prefer the ip_-prefixed key (original entry with favorites).
                # If neither or both are ip_-prefixed, keep the existing one.
                if did.startswith('ip_') and not existing_id.startswith('ip_'):
                    to_drop.append(existing_id)
                    seen[ip] = did
                else:
                    to_drop.append(did)
        # Re-point active_device_id if it was a dropped duplicate.
        if self.active_device_id in to_drop:
            # Find the retained entry for the same IP.
            dropped_ip = None
            for did, info in self.devices.items():
                if did == self.active_device_id:
                    dropped_ip = info.get('ip')
                    break
            if dropped_ip and dropped_ip in seen:
                self.active_device_id = seen[dropped_ip]
        for did in to_drop:
            del self.devices[did]
        if to_drop:
            self.save()
    
    def save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(DEVICES_FILE, 'w') as f:
                json.dump({"devices": self.devices, "active_device_id": self.active_device_id}, f, indent=2)
            return True
        except:
            return False
    
    def add_device(self, device_info):
        ip = device_info['ip']
        # Reuse an existing entry that already has this IP so that the device
        # ID (and therefore its favorites) never change between rescans.
        existing_id = next(
            (did for did, info in self.devices.items() if info.get('ip') == ip),
            None
        )
        device_id = existing_id or device_info.get('serial') or f"ip_{ip.replace('.', '_')}"
        self.devices[device_id] = {
            'name': device_info['name'],
            'ip': ip,
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
