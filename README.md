# Roku Remote TUI

**A professional terminal-based remote control for Roku devices**

![Version](https://img.shields.io/badge/version-2.1.0-blue)
![Python](https://img.shields.io/badge/python-3.7+-green)
![License](https://img.shields.io/badge/license-MIT-blue)

## ✨ Features

- **Fuzzy Launcher** - Press `/` to instantly search and launch apps
- **Favorites** - Save up to 9 apps for one-key launch (1-9 keys)
- **Recent Apps** - Automatic tracking of last 10 launched apps
- **Statistics** - View your most-used apps (Shift+S)
- **Themes** - 5 color schemes to choose from (Shift+T)
- **Full Remote Control** - All buttons: arrows, OK, back, home, volume, etc.
- **Text Input** - Type mode for search boxes and passwords
- **Mouse Support** - Scroll apps with mouse wheel

## 🚀 Quick Start

### Prerequisites
```bash
# Install Roku CLI
npm install -g @dlenroc/roku

# Configure your Roku
roku setup
```

### Installation
```bash
git clone https://github.com/Extended3652/roku-remote-tui.git
cd roku-remote-tui
python3 roku_tui_main.py
```

## ⌨️ Key Shortcuts

| Key | Action |
|-----|--------|
| `?` | Help overlay |
| `/` | Fuzzy launcher |
| `1-9` | Launch favorite |
| `F` + `1-9` | Set favorite |
| `Shift+T` | Cycle themes |
| `Shift+S` | View statistics |
| `Tab` | Switch focus |
| `t` | Typing mode |
| `q` | Quit |

## 🎯 Coming Soon

- [ ] Multi-device support with auto-discovery
- [ ] Macro recording and playback
- [ ] REST API for external control
- [ ] Home Assistant integration
- [ ] WebSocket events

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

## 💡 Support

Like this project? Consider:
- ⭐ Starring the repo
- 🐛 Reporting bugs
- 💰 Supporting development (coming soon)

---

**Made with ❤️ for the Roku community**
