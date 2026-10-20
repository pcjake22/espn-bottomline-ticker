import sys
import traceback
import requests
from datetime import datetime
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QLabel, QMenu, QFrame
)
from PyQt6.QtGui import (
    QAction, QPixmap, QPainter, QFont, QColor, QFontMetrics
)

# Trap and log any uncaught exceptions directly to terminal
def exception_hook(exctype, value, tb):
    print("\n--- UNCAUGHT EXCEPTION ---")
    traceback.print_exception(exctype, value, tb)
    sys.exit(1)

sys.excepthook = exception_hook


class ScoreWorker(QThread):
    """Background worker fetching scores and logo assets to prevent UI freezes."""
    data_ready = pyqtSignal(list, dict)

    def run(self):
        url = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard"
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code != 200:
                return

            data = resp.json()
            parsed = []
            logo_urls = set()

            for event in data.get('events', []):
                comp = event['competitions'][0]
                home = comp['competitors'][0]
                away = comp['competitors'][1]
                
                status = event['status']['type']['shortDetail']
                situation = comp.get('situation', {})
                
                alert = ""
                if situation.get('isPowerPlay'):
                    alert = "POWER PLAY"

                last_play = ""
                if situation.get('lastPlay'):
                    last_play = situation['lastPlay'].get('text', '')

                away_logo = away['team'].get('logo', '')
                home_logo = home['team'].get('logo', '')
                if away_logo:
                    logo_urls.add(away_logo)
                if home_logo:
                    logo_urls.add(home_logo)

                parsed.append({
                    "away_abbr": away['team'].get('abbreviation', ''),
                    "away_score": away.get('score', '0'),
                    "away_logo": away_logo,
                    "home_abbr": home['team'].get('abbreviation', ''),
                    "home_score": home.get('score', '0'),
                    "home_logo": home_logo,
                    "status": status,
                    "alert": alert,
                    "last_play": last_play
                })

            raw_logos = {}
            for l_url in logo_urls:
                try:
                    img_resp = requests.get(l_url, timeout=2)
                    if img_resp.status_code == 200:
                        raw_logos[l_url] = img_resp.content
                except Exception:
                    pass

            self.data_ready.emit(parsed, raw_logos)
        except Exception as e:
            print(f"[Worker] Network error: {e}")


class MarqueeWidget(QWidget):
    """60 FPS continuous crawler that draws inline logos and text with exact spacing."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.segments = []
        self.offset = 0.0
        self.scroll_speed = 1.8
        self.gap = 90
        self.total_width = 0
        self.font = QFont("Segoe UI", 11, QFont.Weight.Bold)

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.advance_scroll)
        self.anim_timer.start(16)

    def set_segments(self, segments):
        self.segments = segments
        self.calculate_metrics()

    def calculate_metrics(self):
        fm = QFontMetrics(self.font)
        width = 0
        for seg in self.segments:
            if seg["type"] == "text":
                seg["width"] = fm.horizontalAdvance(seg["content"])
            elif seg["type"] == "logo":
                seg["width"] = 20
            width += seg["width"] + seg.get("spacing", 0)
        self.total_width = width

    def advance_scroll(self):
        if not self.segments or self.total_width <= 0:
            return
        step = self.total_width + self.gap
        self.offset = (self.offset + self.scroll_speed) % step
        self.update()

    def paintEvent(self, event):
        if not self.segments or self.total_width <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setFont(self.font)

        fm = painter.fontMetrics()
        y_text = int((self.height() + fm.ascent() - fm.descent()) / 2)
        y_logo = int((self.height() - 20) / 2)

        step = self.total_width + self.gap
        start_x = -int(self.offset)
        x = start_x

        while x < self.width():
            curr_x = x
            for seg in self.segments:
                if seg["type"] == "text":
                    painter.setPen(QColor(seg.get("color", "#D6D9E0")))
                    painter.drawText(curr_x, y_text, seg["content"])
                elif seg["type"] == "logo" and seg.get("pixmap"):
                    painter.drawPixmap(curr_x, y_logo, seg["pixmap"])
                curr_x += seg["width"] + seg.get("spacing", 0)
            x += step


class FullBroadcastTicker(QWidget):
    def __init__(self, initial_screen_index=0):
        super().__init__()
        self.games = []
        self.current_game_index = 0
        self.current_screen_index = initial_screen_index
        self.logo_cache = {}

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )

        self.setStyleSheet("""
            QWidget {
                background-color: #0d0e11;
                color: #FFFFFF;
                font-family: 'Segoe UI', Arial, sans-serif;
                border-top: 2px solid #CC0000;
            }
            #brand_badge {
                background-color: #CC0000;
                color: #FFFFFF;
                font-weight: 900;
                font-size: 13px;
                padding: 4px 12px;
                border-radius: 2px;
                letter-spacing: 1px;
            }
            #score_tile {
                background-color: #1a1c23;
                border-radius: 4px;
                padding: 2px 10px;
                font-weight: 800;
                font-size: 15px;
            }
            #game_clock {
                color: #00E676;
                font-weight: 700;
                font-size: 13px;
                padding: 0 8px;
            }
            #alert_badge {
                background-color: #FFB300;
                color: #000000;
                font-weight: 900;
                font-size: 11px;
                padding: 3px 8px;
                border-radius: 3px;
                letter-spacing: 0.5px;
            }
            #clock_label {
                color: #888888;
                font-size: 12px;
                font-weight: 600;
                padding: 0 10px;
            }
            QMenu {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #444444;
                font-size: 13px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
            }
            QMenu::item:selected {
                background-color: #CC0000;
            }
        """)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 0, 12, 0)
        main_layout.setSpacing(10)

        # 1. Left Brand Badge
        self.brand_label = QLabel("NHL BOTTOMLINE")
        self.brand_label.setObjectName("brand_badge")
        main_layout.addWidget(self.brand_label)

        # 2. Featured Game Section
        self.away_logo = QLabel()
        self.away_score = QLabel("---")
        self.away_score.setObjectName("score_tile")

        self.vs_label = QLabel("@")
        self.vs_label.setStyleSheet("color: #666; font-weight: 900;")

        self.home_logo = QLabel()
        self.home_score = QLabel("---")
        self.home_score.setObjectName("score_tile")

        self.game_clock = QLabel("LOADING")
        self.game_clock.setObjectName("game_clock")

        main_layout.addWidget(self.away_logo)
        main_layout.addWidget(self.away_score)
        main_layout.addWidget(self.vs_label)
        main_layout.addWidget(self.home_logo)
        main_layout.addWidget(self.home_score)
        main_layout.addWidget(self.game_clock)

        divider1 = QFrame()
        divider1.setFrameShape(QFrame.Shape.VLine)
        divider1.setStyleSheet("color: #2D3139; max-height: 24px;")
        main_layout.addWidget(divider1)

        # 3. Center Marquee
        self.marquee = MarqueeWidget(self)
        main_layout.addWidget(self.marquee, stretch=1)

        divider2 = QFrame()
        divider2.setFrameShape(QFrame.Shape.VLine)
        divider2.setStyleSheet("color: #2D3139; max-height: 24px;")
        main_layout.addWidget(divider2)

        # 4. Right Status + Clock
        self.alert_badge = QLabel("")
        self.alert_badge.setObjectName("alert_badge")
        self.alert_badge.hide()
        main_layout.addWidget(self.alert_badge)

        self.clock_label = QLabel("")
        self.clock_label.setObjectName("clock_label")
        main_layout.addWidget(self.clock_label)

        # Position on monitor
        self.move_to_screen(self.current_screen_index)

        # Clocks & Polling
        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self.update_clock)
        self.time_timer.start(1000)
        self.update_clock()

        self.cycle_timer = QTimer(self)
        self.cycle_timer.timeout.connect(self.cycle_featured_game)
        self.cycle_timer.start(6000)

        self.worker = None
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.start_fetch)
        self.poll_timer.start(15000)
        self.start_fetch()

    def update_clock(self):
        self.clock_label.setText(datetime.now().strftime("%I:%M:%S %p"))

    def move_to_screen(self, screen_index):
        screens = QApplication.screens()
        if screen_index < len(screens):
            self.current_screen_index = screen_index
            target_screen = screens[screen_index]
        else:
            self.current_screen_index = 0
            target_screen = screens[0]

        geo = target_screen.geometry()
        taskbar_height = 48

        self.setGeometry(
            geo.x(),
            geo.y() + geo.height() - taskbar_height,
            geo.width(),
            taskbar_height
        )

    def start_fetch(self):
        if self.worker and self.worker.isRunning():
            return
        self.worker = ScoreWorker()
        self.worker.data_ready.connect(self.on_data_loaded)
        self.worker.start()

    def on_data_loaded(self, parsed_games, raw_logos):
        for url, data in raw_logos.items():
            if url not in self.logo_cache:
                pix = QPixmap()
                pix.loadFromData(data)
                self.logo_cache[url] = {
                    26: pix.scaled(26, 26, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation),
                    20: pix.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                }

        self.games = parsed_games
        self.update_crawler_segments()
        if self.away_score.text() == "---":
            self.cycle_featured_game()

    def get_pixmap(self, url, size=26):
        if url in self.logo_cache and size in self.logo_cache[url]:
            return self.logo_cache[url][size]
        return None

    def update_crawler_segments(self):
        segments = []
        for i, g in enumerate(self.games):
            away_px = self.get_pixmap(g["away_logo"], size=20)
            home_px = self.get_pixmap(g["home_logo"], size=20)

            # Away Team
            if away_px:
                segments.append({"type": "logo", "pixmap": away_px, "spacing": 8})
            segments.append({"type": "text", "content": f"{g['away_abbr']} {g['away_score']}  -  ", "spacing": 4})

            # Home Team
            segments.append({"type": "text", "content": f"{g['home_score']} {g['home_abbr']}", "spacing": 8})
            if home_px:
                segments.append({"type": "logo", "pixmap": home_px, "spacing": 12})

            # Details
            detail_str = f"({g['status'].upper()})"
            if g["last_play"]:
                detail_str += f" [{g['last_play']}]"
            segments.append({"type": "text", "content": detail_str, "color": "#9E9E9E", "spacing": 24})

            # Divider Star
            segments.append({"type": "text", "content": "★", "color": "#CC0000", "spacing": 24})

        self.marquee.set_segments(segments)

    def cycle_featured_game(self):
        if not self.games:
            return
        
        game = self.games[self.current_game_index]
        self.away_score.setText(f"{game['away_abbr']}  {game['away_score']}")
        self.home_score.setText(f"{game['home_abbr']}  {game['home_score']}")
        self.game_clock.setText(game['status'].upper())

        away_px = self.get_pixmap(game['away_logo'], size=26)
        if away_px:
            self.away_logo.setPixmap(away_px)
            self.away_logo.show()
        else:
            self.away_logo.hide()

        home_px = self.get_pixmap(game['home_logo'], size=26)
        if home_px:
            self.home_logo.setPixmap(home_px)
            self.home_logo.show()
        else:
            self.home_logo.hide()

        if game["alert"]:
            self.alert_badge.setText(f"⚡ {game['alert']}")
            self.alert_badge.show()
        else:
            self.alert_badge.hide()

        self.current_game_index = (self.current_game_index + 1) % len(self.games)

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        screen_menu = menu.addMenu("Move to Screen...")
        screens = QApplication.screens()
        for i, s in enumerate(screens):
            label = f"Screen {i} ({s.name()})"
            if i == self.current_screen_index:
                label += " ✓"
            action = QAction(label, self)
            action.triggered.connect(lambda checked, idx=i: self.move_to_screen(idx))
            screen_menu.addAction(action)

        action_refresh = QAction("Force Score Refresh", self)
        action_refresh.triggered.connect(self.start_fetch)
        menu.addAction(action_refresh)

        menu.addSeparator()

        action_minimize = QAction("Minimize / Hide", self)
        action_minimize.triggered.connect(self.showMinimized)
        menu.addAction(action_minimize)

        action_exit = QAction("Exit Ticker", self)
        action_exit.triggered.connect(QApplication.instance().quit)
        menu.addAction(action_exit)

        menu.exec(event.globalPos())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Change initial_screen_index (0, 1, or 2) to your preferred monitor,
    # or right-click anywhere on the bar -> 'Move to Screen...' to shift it live.
    ticker = FullBroadcastTicker(initial_screen_index=0)
    ticker.show()
    sys.exit(app.exec())