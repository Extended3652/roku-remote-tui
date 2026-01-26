"""Simple Roku CLI wrapper."""
import subprocess

class RokuCLI:
    def __init__(self):
        self.command_count = 0
    
    def run(self, args, capture=False, timeout=10.0):
        cmd = ["roku"] + args
        try:
            self.command_count += 1
            if capture:
                return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            else:
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout)
                return None
        except:
            return None
