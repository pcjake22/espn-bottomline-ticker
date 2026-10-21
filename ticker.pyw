import sys
import traceback
import requests
from datetime import datetime
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QMenu, QFrame
)
from PyQt6.QtGui import (
    QAction, QPixmap, QPainter, QFont, QColor, QFontMetrics, QLinearGradient
)

def exception_hook(exctype, value, tb):
    print("\n--- UNCAUGHT EXCEPTION ---")
    traceback.print_exception(exctype, value, tb)
    sys.exit(1)

sys.excepthook = exception_hook

# Official primary team colors for dynamic score tiles
NHL_COLORS = {
    "ANA": "#F47A38", "ARI": "#8C2633", "BOS": "#FFB81C", "BUF": "#002654",
    "CGY": "#C8102E", "CAR": "#CC0000", "CHI": "#CF0A2C", "COL": "#6F263D",
    "CBJ": "#002654", "DAL": "#006847", "DET": "#CE1126", "EDM": "#041E42",
    "FLA": "#C8102E", "LAK": "#111111", "MIN": "#154734", "MTL": "#AF1E2D",
    "NSH": "#FFB81C", "NJD": "#CE1126", "NYI": "#00539B", "NYR": "#0038A8",
    "OTT": "#C52032", "PHI": "#F74902", "PIT": "#FCB514", "SJS": "#006D75",
    "SEA": "#001628", "STL": "#002F87", "TBL": "#002868", "TOR": "#00205B",
    "UTA": "#6CACE4", "VAN": "#00205B", "VGK": "#B4975A", "WSH": "#041E42",
    "WPG": "#041E42"
}

class BottomlineBadge(QWidget):
    """Broadcast-style two-tier 'NHL BOTTOMLINE' pill badge."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(140, 36)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # Red gradient background plate
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, QColor("#D31027"))
        grad.setColorAt(1.0, QColor("#990012"))

        painter.setPen(QColor("#FF4D5E"))
        painter.setBrush(grad)
        painter.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, 4, 4)

        # Top line: "NHL"
        font_top = QFont("Segoe UI", 8, QFont.Weight.Black)
        font_top.setItalic(True)
        painter.setFont(font_top)
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(10, 14, "NHL")

        # Bottom banner: "BOTTOMLINE"
        font_bottom = QFont("Segoe UI", 11, QFont.Weight.Black)
        font_bottom.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.2)
        painter.setFont(font_bottom)
        painter.drawText(10, 30, "BOTTOMLINE")


class ScoreWorker(QThread):
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

                away_abbr = away['team'].get('abbreviation', '')
                home_abbr = home['team'].get('abbreviation', '')

                away_color = f"#{away['team'].get('color', '')}" if away['team'].get('color') else NHL_COLORS.get(away_abbr, "#222222")
                home_color = f"#{home['team'].get('color', '')}" if home['team'].get('color') else NHL_COLORS.get(home_abbr, "#222222")

                away_logo = away['team'].get('logo', '')
                home_logo = home['team'].get('logo', '')
                if away_logo:
                    logo_urls.add(away_logo)
                if home_logo:
                    logo_urls.add(home_logo)

                parsed.append({
                    "away_abbr": away_abbr,
                    "away_score": away.get('score', '0'),
                    "away_logo": away_logo,
                    "away_color": away_color,
                    "home_abbr": home_abbr,
                    "home_score": home.get('score', '0'),
                    "home_logo": home_logo,
                    "home_color": home_color,
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
                seg["width"] = 22
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
        y_logo = int((self.height() - 22) / 2)

        step = self.total_width + self.gap
        start_x = -int(self.offset)
        x = start_x

        while x < self.width():
            curr_x = x
            for seg in self.segments:
                if seg["type"] == "text":
                    painter.setPen(QColor(seg.get("color", "#E5E7EB")))
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

        # Scoped stylesheet: Only FullBroadcastTicker gets the top border
        self.setStyleSheet("""
            FullBroadcastTicker {
                background-color: #0b0c0e;
                border-top: 2px solid #CC0000;
            }
            QLabel {
                color: #FFFFFF;
                font-family: 'Segoe UI', Arial, sans-serif;
                border: none;
            }
            #featured_capsule {
                background-color: #12141a;
                border: 1px solid #232733;
                border-radius: 6px;
            }
            #crawler_capsule {
                background-color: #101217;
                border: 1px solid #1f232e;
                border-radius: 6px;
            }
            #game_clock {
                color: #00E676;
                font-weight: 800;
                font-size: 13px;
                padding: 0 10px;
                border: none;
            }
            #alert_badge {
                background-color: #FBBF24;
                color: #000000;
                font-weight: 900;
                font-size: 11px;
                padding: 4px 10px;
                border-radius: 4px;
                letter-spacing: 0.5px;
                border: none;
            }
            #clock_label {
                background-color: #12141a;
                border: 1px solid #232733;
                border-radius: 4px;
                color: #CBD5E1;
                font-size: 12px;
                font-weight: 700;
                padding: 4px 10px;
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
        main_layout.setContentsMargins(10, 4, 10, 4)
        main_layout.setSpacing(10)

        # 1. Authentic TV Badge Pill
        self.brand_badge = BottomlineBadge(self)
        main_layout.addWidget(self.brand_badge)

        # 2. Featured Game Capsule
        self.featured_capsule = QFrame()
        self.featured_capsule.setObjectName("featured_capsule")
        capsule_layout = QHBoxLayout(self.featured_capsule)
        capsule_layout.setContentsMargins(4, 2, 8, 2)
        capsule_layout.setSpacing(6)

        # Away Block
        self.away_block = QFrame()
        away_layout = QHBoxLayout(self.away_block)
        away_layout.setContentsMargins(6, 2, 6, 2)
        away_layout.setSpacing(6)
        self.away_logo = QLabel()
        self.away_abbr = QLabel("---")
        self.away_abbr.setStyleSheet("font-weight: 900; font-size: 13px; border: none;")
        self.away_score = QLabel("0")
        self.away_score.setStyleSheet("font-weight: 900; font-size: 15px; background: rgba(0,0,0,0.45); padding: 1px 7px; border-radius: 3px; border: none;")
        away_layout.addWidget(self.away_logo)
        away_layout.addWidget(self.away_abbr)
        away_layout.addWidget(self.away_score)

        # VS divider
        self.vs_label = QLabel("@")
        self.vs_label.setStyleSheet("color: #6B7280; font-weight: 900; font-size: 12px; border: none;")

        # Home Block
        self.home_block = QFrame()
        home_layout = QHBoxLayout(self.home_block)
        home_layout.setContentsMargins(6, 2, 6, 2)
        home_layout.setSpacing(6)
        self.home_logo = QLabel()
        self.home_abbr = QLabel("---")
        self.home_abbr.setStyleSheet("font-weight: 900; font-size: 13px; border: none;")
        self.home_score = QLabel("0")
        self.home_score.setStyleSheet("font-weight: 900; font-size: 15px; background: rgba(0,0,0,0.45); padding: 1px 7px; border-radius: 3px; border: none;")
        home_layout.addWidget(self.home_logo)
        home_layout.addWidget(self.home_abbr)
        home_layout.addWidget(self.home_score)

        self.game_clock = QLabel("LOADING")
        self.game_clock.setObjectName("game_clock")

        capsule_layout.addWidget(self.away_block)
        capsule_layout.addWidget(self.vs_label)
        capsule_layout.addWidget(self.home_block)
        capsule_layout.addWidget(self.game_clock)
        main_layout.addWidget(self.featured_capsule)

        # 3. Crawler in Capsule
        self.crawler_capsule = QFrame()
        self.crawler_capsule.setObjectName("crawler_capsule")
        crawler_layout = QHBoxLayout(self.crawler_capsule)
        crawler_layout.setContentsMargins(8, 0, 8, 0)
        self.marquee = MarqueeWidget(self)
        crawler_layout.addWidget(self.marquee)
        main_layout.addWidget(self.crawler_capsule, stretch=1)

        # 4. Alert & Clock
        self.alert_badge = QLabel("")
        self.alert_badge.setObjectName("alert_badge")
        self.alert_badge.hide()
        main_layout.addWidget(self.alert_badge)

        self.clock_label = QLabel("")
        self.clock_label.setObjectName("clock_label")
        main_layout.addWidget(self.clock_label)

        self.move_to_screen(self.current_screen_index)

        # Timers
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
        self.clock_label.setText(datetime.now().strftime("%I:%M:%S"))

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
                    24: pix.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation),
                    20: pix.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                }

        self.games = parsed_games
        self.update_crawler_segments()
        if self.away_abbr.text() == "---":
            self.cycle_featured_game()

    def get_pixmap(self, url, size=24):
        if url in self.logo_cache and size in self.logo_cache[url]:
            return self.logo_cache[url][size]
        return None

    def update_crawler_segments(self):
        segments = []
        for i, g in enumerate(self.games):
            away_px = self.get_pixmap(g["away_logo"], size=20)
            home_px = self.get_pixmap(g["home_logo"], size=20)

            if away_px:
                segments.append({"type": "logo", "pixmap": away_px, "spacing": 6})
            segments.append({"type": "text", "content": f"{g['away_abbr']} {g['away_score']}  -  ", "spacing": 4})

            segments.append({"type": "text", "content": f"{g['home_score']} {g['home_abbr']}", "spacing": 6})
            if home_px:
                segments.append({"type": "logo", "pixmap": home_px, "spacing": 10})

            detail_str = f"({g['status'].upper()})"
            if g["last_play"]:
                detail_str += f" [{g['last_play']}]"
            segments.append({"type": "text", "content": detail_str, "color": "#94A3B8", "spacing": 22})

            segments.append({"type": "text", "content": "★", "color": "#CC0000", "spacing": 22})

        self.marquee.set_segments(segments)

    def cycle_featured_game(self):
        if not self.games:
            return
        
        game = self.games[self.current_game_index]

        # Explicitly set border: none so team blocks never draw lines above scores
        self.away_block.setStyleSheet(f"""
            QFrame {{
                background-color: {game['away_color']};
                border-radius: 4px;
                border: none;
            }}
        """)
        self.home_block.setStyleSheet(f"""
            QFrame {{
                background-color: {game['home_color']};
                border-radius: 4px;
                border: none;
            }}
        """)

        self.away_abbr.setText(game['away_abbr'])
        self.away_score.setText(game['away_score'])
        self.home_abbr.setText(game['home_abbr'])
        self.home_score.setText(game['home_score'])
        self.game_clock.setText(game['status'].upper())

        away_px = self.get_pixmap(game['away_logo'], size=24)
        if away_px:
            self.away_logo.setPixmap(away_px)
            self.away_logo.show()
        else:
            self.away_logo.hide()

        home_px = self.get_pixmap(game['home_logo'], size=24)
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
    ticker = FullBroadcastTicker(initial_screen_index=0)
    ticker.show()
    sys.exit(app.exec())