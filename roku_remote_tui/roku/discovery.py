"""Roku device discovery via network scanning."""
import socket
import concurrent.futures
from urllib.request import urlopen
import re


def get_local_network():
    """Auto-detect local network prefix."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        network_prefix = '.'.join(local_ip.split('.')[:-1])
        return network_prefix, local_ip
    finally:
        s.close()


def check_roku(ip, timeout=0.5):
    """Check if IP has a Roku device."""
    try:
        url = f"http://{ip}:8060/query/device-info"
        response = urlopen(url, timeout=timeout)
        data = response.read().decode('utf-8')
        
        if 'Roku' in data or 'roku' in data:
            # Extract device info
            name_match = re.search(r'<friendly-device-name>([^<]+)</friendly-device-name>', data)
            model_match = re.search(r'<model-name>([^<]+)</model-name>', data)
            serial_match = re.search(r'<serial-number>([^<]+)</serial-number>', data)
            
            return {
                'ip': ip,
                'name': name_match.group(1) if name_match else "Roku Device",
                'model': model_match.group(1) if model_match else "Unknown",
                'serial': serial_match.group(1) if serial_match else None
            }
    except:
        pass
    return None


def discover_devices(network_prefix=None, max_workers=50, callback=None):
    """
    Discover Roku devices on the network.
    
    Args:
        network_prefix: Network to scan (e.g., "192.168.1"). Auto-detected if None.
        max_workers: Number of parallel scanning threads
        callback: Optional function to call when device is found
    
    Returns:
        List of device dicts
    """
    if network_prefix is None:
        network_prefix, _ = get_local_network()
    
    found = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(check_roku, f"{network_prefix}.{i}") 
            for i in range(1, 255)
        ]
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                found.append(result)
                if callback:
                    callback(result)
    
    return sorted(found, key=lambda d: d['ip'])


def quick_check(ip):
    """Quickly check if a specific IP is a Roku (for known devices)."""
    return check_roku(ip, timeout=1.0)
