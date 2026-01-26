"""Color theme management."""
import curses

THEMES = {
    "default": {"name": "Default", "colors": {"title": 1, "border": 5, "border_active": 6, "text": 5, "selected": 6, "favorite": 3, "status": 3, "message": 5, "error": 4, "success": 2, "help": 3}},
    "dark": {"name": "Dark", "colors": {"title": 4, "border": 5, "border_active": 1, "text": 5, "selected": 1, "favorite": 3, "status": 4, "message": 5, "error": 4, "success": 2, "help": 3}},
    "monokai": {"name": "Monokai", "colors": {"title": 6, "border": 5, "border_active": 2, "text": 5, "selected": 6, "favorite": 3, "status": 2, "message": 5, "error": 4, "success": 2, "help": 1}}
}

class ThemeManager:
    def __init__(self):
        self.current_theme = "default"
        self.themes = THEMES
    
    def get_color(self, element):
        theme = self.themes.get(self.current_theme, self.themes["default"])
        return theme["colors"].get(element, 5)
    
    def next_theme(self):
        theme_names = list(self.themes.keys())
        current_idx = theme_names.index(self.current_theme)
        next_idx = (current_idx + 1) % len(theme_names)
        self.current_theme = theme_names[next_idx]
        return self.themes[self.current_theme]["name"]
    
    def get_theme_name(self):
        return self.themes[self.current_theme]["name"]
