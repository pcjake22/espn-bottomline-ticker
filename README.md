# NHL BottomLine Taskbar Ticker

![NHL Bottomline Ticker Banner](assets/banner.png)

[![Latest Release](https://img.shields.io/github/v/release/pcjake22/nhl-bottomline-ticker?style=for-the-badge&color=CC0000)](https://github.com/pcjake22/nhl-bottomline-ticker/releases/latest)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-blue?style=for-the-badge)](https://github.com/pcjake22/nhl-bottomline-ticker)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PyQt6-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://pypi.org/project/PyQt6/)

A lightweight broadcast-style bottom ticker that docks directly over your physical taskbar on any monitor. Features live ESPN scores, period clocks, active power-play indicators, and an unbroken 60 FPS around-the-league crawl with official team logos.

---

## ⚡ Quick Start (No Python Required)

If you just want to run the ticker on Windows without installing code dependencies:

1. Download **[`ticker.exe`](https://github.com/pcjake22/nhl-bottomline-ticker/releases/latest/download/ticker.exe)** from the Releases page.
2. Double-click `ticker.exe` to launch.
3. **Right-click** anywhere on the bar to switch monitors, force a score refresh, or close the app.

---

## 🛠️ Features

- **Full-Width Broadcast Ribbon:** Replaces empty taskbar dead-space with a TV-styled ESPN scorebug.
- **Continuous 60 FPS Crawl:** Custom hardware-accelerated ticker loop that scrolls scores, shots, and play events with zero text overlapping.
- **Asynchronous Background Polling:** Fetches data and team logos on background threads so animations remain completely smooth.
- **Dynamic Multi-Monitor Switching:** Instantly jump between connected screens via the right-click menu.
- **Live Situational Alerts:** Flags power plays and last-play goal events automatically.

---

## 💻 Manual Installation (From Source)

```bash
# 1. Clone the repository
git clone [https://github.com/pcjake22/nhl-bottomline-ticker.git](https://github.com/pcjake22/nhl-bottomline-ticker.git)
cd nhl-bottomline-ticker

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the ticker
python ticker.py