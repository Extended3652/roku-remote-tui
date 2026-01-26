"""Simple Roku CLI wrapper."""
import subprocess

class RokuCLI:
    def __init__(self, device_ip=None):
        self.command_count = 0
        self.device_ip = device_ip
    
    def set_device(self, device_ip):
        """Change the target device IP."""
        self.device_ip = device_ip
    
    def run(self, args, capture=False, timeout=10.0):
        cmd = ["roku"]
        
        # Add device IP if set
        if self.device_ip:
            cmd.extend(["--ip", self.device_ip])
        
        cmd.extend(args)
        
        try:
            self.command_count += 1
            if capture:
                return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            else:
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout)
                return None
        except:
            return None
