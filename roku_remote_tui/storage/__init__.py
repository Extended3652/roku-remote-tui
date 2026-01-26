"""Storage layer."""
from .favorites import FavoritesManager
from .recents import RecentsManager
from .stats import StatsManager
from .devices import DeviceManager
__all__ = ['FavoritesManager', 'RecentsManager', 'StatsManager', 'DeviceManager']
