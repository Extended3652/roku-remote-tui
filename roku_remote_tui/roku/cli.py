"""Roku ECP (External Control Protocol) client - no external CLI dependency."""
import urllib.request
import urllib.parse
import json
import xml.etree.ElementTree as ET


class _Result:
    """Mimics subprocess.CompletedProcess for capture mode."""
    def __init__(self, stdout="", returncode=0):
        self.stdout = stdout
        self.returncode = returncode
        self.stderr = ""


class RokuCLI:
    def __init__(self, device_ip=None):
        self.command_count = 0
        self.device_ip = device_ip
        self.last_error = None

    def set_device(self, device_ip):
        """Change the target device IP."""
        self.device_ip = device_ip

    def run(self, args, capture=False, timeout=10.0):
        """Execute a Roku ECP command."""
        if not args:
            return None
        self.command_count += 1
        self.last_error = None
        cmd = args[0]

        if cmd == "home":
            return self._keypress("Home", timeout)
        elif cmd == "power":
            return self._keypress("Power", timeout)
        elif cmd == "nav":
            direction = args[1] if len(args) > 1 else "up"
            key_map = {"up": "Up", "down": "Down", "left": "Left", "right": "Right"}
            key = key_map.get(direction.lower(), direction.capitalize())
            return self._keypress(key, timeout)
        elif cmd == "ok":
            return self._keypress("Select", timeout)
        elif cmd == "back":
            return self._keypress("Back", timeout)
        elif cmd == "info":
            return self._keypress("Info", timeout)
        elif cmd == "replay":
            return self._keypress("InstantReplay", timeout)
        elif cmd == "play":
            return self._keypress("Play", timeout)
        elif cmd == "rev":
            return self._keypress("Rev", timeout)
        elif cmd == "fwd":
            return self._keypress("Fwd", timeout)
        elif cmd == "mute":
            return self._keypress("VolumeMute", timeout)
        elif cmd == "vol":
            direction = args[1] if len(args) > 1 else "up"
            key = "VolumeUp" if direction.lower() == "up" else "VolumeDown"
            return self._keypress(key, timeout)
        elif cmd == "keyup":
            raw = args[1] if len(args) > 1 else "Select"
            key_map = {"select": "Select", "home": "Home"}
            key = key_map.get(raw.lower(), raw.capitalize())
            return self._keyup(key, timeout)
        elif cmd == "keydown":
            raw = args[1] if len(args) > 1 else "Select"
            key_map = {"select": "Select", "home": "Home"}
            key = key_map.get(raw.lower(), raw.capitalize())
            return self._keydown(key, timeout)
        elif cmd == "launch":
            app_id = args[1] if len(args) > 1 else ""
            ok = self._post(f"/launch/{urllib.parse.quote(str(app_id), safe='')}", timeout)
            return True if ok else None
        elif cmd == "type":
            text = args[1] if len(args) > 1 else ""
            return self._type_text(text, timeout)
        elif cmd == "apps":
            return self._get_apps(timeout)
        return None

    # ------------------------------------------------------------------ #
    #  Internal HTTP helpers                                               #
    # ------------------------------------------------------------------ #

    def _base_url(self):
        return f"http://{self.device_ip}:8060"

    def _post(self, path, timeout=5.0):
        if not self.device_ip:
            self.last_error = "No device IP configured"
            return False
        try:
            url = self._base_url() + path
            req = urllib.request.Request(url, data=b"", method="POST")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status == 200
        except Exception as e:
            self.last_error = str(e)
            return False

    def _keypress(self, key, timeout=5.0):
        ok = self._post(f"/keypress/{key}", timeout)
        return True if ok else None

    def _keyup(self, key, timeout=5.0):
        ok = self._post(f"/keyup/{key}", timeout)
        return True if ok else None

    def _keydown(self, key, timeout=5.0):
        ok = self._post(f"/keydown/{key}", timeout)
        return True if ok else None

    def _type_text(self, text, timeout=5.0):
        for char in text:
            encoded = urllib.parse.quote(char, safe="")
            if not self._post(f"/keypress/Lit_{encoded}", timeout):
                return None
        return True

    def _get_apps(self, timeout=10.0):
        if not self.device_ip:
            self.last_error = "No device IP configured"
            return None
        try:
            url = self._base_url() + "/query/apps"
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                data = resp.read().decode("utf-8")
            root = ET.fromstring(data)
            apps = []
            for app_el in root.findall("app"):
                app_id = app_el.get("id", "")
                app_type = app_el.get("type", "appl")
                name = (app_el.text or "").strip()
                apps.append({"name": name, "arg": app_id, "type": app_type})
            return _Result(stdout=json.dumps(apps), returncode=0)
        except Exception as e:
            self.last_error = str(e)
            return None
