# ESPN BottomLine Ticker & Multiview

![ESPN BottomLine Ticker Banner](assets/banner-v1.2.png)

[![Latest Release](https://img.shields.io/github/v/release/pcjake22/nhl-bottomline-ticker?style=for-the-badge&color=CC0000)](https://github.com/pcjake22/nhl-bottomline-ticker/releases/latest)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-blue?style=for-the-badge)](https://github.com/pcjake22/nhl-bottomline-ticker)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PyQt6-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://pypi.org/project/PyQt6/)

A lightweight broadcast-style bottom ticker that docks directly over your physical taskbar on any monitor. Features real-time ESPN scoreboard feeds, period/quarter clocks, situational alerts (Power Plays, Red Zones), and an unbroken 60 FPS around-the-league crawl with official team logos across NHL, NFL, NBA, and MLB—plus an automated 4-way stream multiview grid with native Windows quadrant snapping.

---

## ⚡ Quick Start (No Python Required)

1. Download **[`ESPN-BottomLine.exe`](https://github.com/pcjake22/nhl-bottomline-ticker/releases/latest/download/ESPN-BottomLine.exe)** from the Releases tab.
2. Double-click `ESPN-BottomLine.exe` to run.
3. Left-click the brand badge to jump between sports, or right-click anywhere for monitor settings, controls, and multiview launch.

---

## 🎮 Controls

- **Left-Click Brand Badge:** Instantly toggle between **NHL** (Red), **NFL** (Blue), **NBA** (Orange), and **MLB** (Green).
- **Right-Click Anywhere:**
  * **📺 Launch 4-Way Multiview...:** Opens the multiview setup menu to choose target screen and 4 streaming URLs.
  * **Switch Sport:** Choose any league directly from the menu.
  * **Move to Screen:** Transfer the ticker ribbon across multi-monitor setups.
  * **Force Score Refresh:** Manually fetch the latest data immediately.
  * **Minimize / Exit:** Hide or quit the application.

---

## 📺 4-Way Multiview & Firefox Setup

The multiview grid opens 4 stream windows and docks them directly into a 2x2 grid sitting flush on top of the 48px ticker.

### Requirements:
- **Mozilla Firefox:** Firefox is required for automated multi-window quadrant launch. The app auto-detects Firefox across standard installations, PATH, and registry entries.
- **Enable Windowed Fullscreen (Recommended):**  
  To allow game streams to expand to fill **only their snapped quadrant** without overtaking the entire monitor:
  1. Open Firefox, type `about:config` in the address bar, and press Enter.
  2. Accept the risk prompt and search for:
     ```text
     full-screen-api.ignore-widgets
     ```
  3. Double-click to set it to **`true`**.
- **Windows Snap Windows:** Ensure OS snapping is toggled ON in **Windows Settings → System → Multitasking → Snap windows**.

```text
+-----------------------+-----------------------+
|                       |                       |
|      Top-Left         |       Top-Right       |
|                       |                       |
+-----------------------+-----------------------+
|                       |                       |
|     Bottom-Left       |     Bottom-Right      |
|                       |                       |
+===============================================+
| [ESPN BOTTOMLINE]  COL 3 @ NJ 4  ★  BOS 2-1 DAL |  <- 48px Ticker
+===============================================+
```
---

## ✨ Features

* **Authentic NHL Broadcast Experience:** Full coverage for hockey scores, power plays, and continuous crawls with official NHL team branding and dynamic team colors.
* **Multi-Sport Flexibility:** Easily flip from hockey night to Sunday football, hoops, or baseball with live scoreboards for NFL, NBA, and MLB.
* **Dynamic Sport Themes:** Instant visual feedback when changing leagues with dedicated theme accents (NHL Crimson, NFL Blue, NBA Orange, MLB Green).
* **Continuous 60 FPS Crawl:** Hardware-accelerated ticker loop with official team logos and smooth scrolling.
* **Parallel Asset Fetching:** Multithreaded background loading ensures instant sport switching with zero UI freezing.
* **Multi-Monitor Awareness:** Docks seamlessly to the bottom edge of any chosen display.

---

## 💻 Manual Installation (Run from Source)

```bash
# 1. Clone repository
git clone [https://github.com/pcjake22/nhl-bottomline-ticker.git](https://github.com/pcjake22/nhl-bottomline-ticker.git)
cd nhl-bottomline-ticker

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch application
python ticker.py
