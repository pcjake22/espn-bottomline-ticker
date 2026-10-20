NHL BottomLine Taskbar Ticker

A live ESPN-styled NHL TV score ribbon and crawler overlay built with Python and PyQt6. Docks directly over your physical taskbar on any monitor, featuring live scores, game status, power play badges, and an inline crawl with team logos.

FEATURES

• Full Monitor TV Ribbon: Frameless, always-on-top layout modeled after sports broadcasts.

• Continuous 60 FPS Crawl: Around-the-league ticker with inline team logos and live play updates.

• Non-Blocking Background Fetch: Score and logo assets update without UI stutter.

• Multi-Monitor Support: Right-click context menu lets you instantly swap the ticker to any connected display.

INSTALLATION & SETUP

    Clone the repository:
    git clone https://github.com/pcjake22/nhl-bottomline-ticker.git
    cd nhl-bottomline-ticker

    Install dependencies:
    pip install -r requirements.txt

    Run the ticker:
    python ticker.py

Tip for Windows users: Rename ticker.py to ticker.pyw (or launch via pythonw ticker.py) to run it silently in the background without a terminal window.
