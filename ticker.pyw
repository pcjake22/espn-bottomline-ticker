import sys
import traceback
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QLabel, QMenu, QFrame
)
from PyQt6.QtGui import (
    QAction, QPixmap, QPainter, QFont, QColor, QFontMetrics, QLinearGradient
)

def exception_hook(exctype, value, tb):
    print("\n--- UNCAUGHT EXCEPTION ---")
    traceback.print_exception(exctype, value, tb)
    sys.exit(1)

sys.excepthook = exception_hook

# Supported sports configurations with dynamic theme colors & endpoints
SPORTS_CONFIG = {
    "NHL": {
        "label": "NHL",
        "primary_color": "#CC0000",
        "gradient_top": "#D31027",
        "gradient_bottom": "#990012",
        "url": "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard",
        "alert_key": "isPowerPlay",
        "alert_label": "POWER PLAY"
    },
    "NFL": {
        "label": "NFL",
        "primary_color": "#013369",
        "gradient_top": "#0D47A1",
        "gradient_bottom": "#012148",
        "url": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
        "alert_key": "isRedZone",
        "alert_label": "RED ZONE"
    },
    "NBA": {
        "label": "NBA",
        "primary_color": "#FF6600",
        "gradient_top": "#FF7A00",
        "gradient_bottom": "#CC4400",
        "url": "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
        "alert_key": None,
        "alert_label": ""
    },
    "MLB": {
        "label": "MLB",
        "primary_color": "#0A6E3F",
        "gradient_top": "#11854F",
        "gradient_bottom": "#074D2B",
        "url": "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard",
        "alert_key": None,
        "alert_label": ""
    }
}


class BottomlineBadge(QWidget):
    """Broadcast badge that displays current sport and emits a click event."""
    clicked = pyqtSignal()

    def __init__(self, sport_key="NHL", parent=None):
        super().__init__(parent)
        self.sport_key = sport_key
        self.setFixedSize(144, 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_sport(self, sport_key):
        self.sport_key = sport_key
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        cfg = SPORTS_CONFIG.get(self.sport_key, SPORTS_CONFIG["NHL"])

        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, QColor(cfg["gradient_top"]))
        grad.setColorAt(1.0, QColor(cfg["gradient_bottom"]))

        painter.setPen(QColor(cfg["primary_color"]))
        painter.setBrush(grad)
        painter.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, 4, 4)

        # Top line: Sport code
        font_top = QFont("Segoe UI", 8, QFont.Weight.Black)
        font_top.setItalic(True)
        painter.setFont(font_top)
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(10, 14, cfg["label"])

        # Bottom line: "BOTTOMLINE"
        font_bottom = QFont("Segoe UI", 11, QFont.Weight.Black)
        font_bottom.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.1)
        painter.setFont(font_bottom)
        painter.drawText(10, 30, "BOTTOMLINE")


class ScoreWorker(QThread):
    data_ready = pyqtSignal(list, dict, str)

    def __init__(self, sport_key):
        super().__init__()
        self.sport_key = sport_key

    def run(self):
        cfg = SPORTS_CONFIG.get(self.sport_key, SPORTS_CONFIG["NHL"])
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            resp = requests.get(cfg["url"], headers=headers, timeout=5)
            if resp.status_code != 200:
                return

            data = resp.json()
            parsed = []
            logo_urls = set()

            for event in data.get('events', []):
                comps = event.get('competitions', [])
                if not comps:
                    continue
                comp = comps[0]
                competitors = comp.get('competitors', [])
                if len(competitors) < 2:
                    continue

                home = competitors[0]
                away = competitors[1]
                
                status = event.get('status', {}).get('type', {}).get('shortDetail', 'TBD')
                situation = comp.get('situation', {})
                
                alert = ""
                if cfg["alert_key"] and situation.get(cfg["alert_key"]):
                    alert = cfg["alert_label"]

                last_play = ""
                if situation.get('lastPlay'):
                    last_play = situation['lastPlay'].get('text', '')

                away_abbr = away['team'].get('abbreviation', 'AWY')
                home_abbr = home['team'].get('abbreviation', 'HME')

                away_color = f"#{away['team'].get('color', '')}" if away['team'].get('color') else "#222634"
                home_color = f"#{home['team'].get('color', '')}" if home['team'].get('color') else "#222634"

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
            def fetch_single_logo(url):
                try:
                    r = requests.get(url, headers=headers, timeout=2)
                    if r.status_code == 200:
                        return (url, r.content)
                except Exception:
                    pass
                return None

            with ThreadPoolExecutor(max_workers=10) as executor:
                results = executor.map(fetch_single_logo, logo_urls)
                for res in results:
                    if res:
                        raw_logos[res[0]] = res[1]

            self.data_ready.emit(parsed, raw_logos, self.sport_key)
        except Exception as e:
            print(f"[ScoreWorker - {self.sport_key}] Network error: {e}")


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


class MultiSportTicker(QWidget):
    def __init__(self, initial_screen_index=0):
        super().__init__()
        self.sports = list(SPORTS_CONFIG.keys())
        self.current_sport_idx = 0
        self.current_sport = self.sports[self.current_sport_idx]

        self.games = []
        self.current_game_index = 0
        self.current_screen_index = initial_screen_index
        self.logo_cache = {}

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 4, 10, 4)
        main_layout.setSpacing(10)

        # 1. Sport Brand Badge
        self.brand_badge = BottomlineBadge(self.current_sport, self)
        self.brand_badge.clicked.connect(self.cycle_sport)
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

        # Divider
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

        # 3. Crawler Capsule
        self.crawler_capsule = QFrame()
        self.crawler_capsule.setObjectName("crawler_capsule")
        crawler_layout = QHBoxLayout(self.crawler_capsule)
        crawler_layout.setContentsMargins(8, 0, 8, 0)
        self.marquee = MarqueeWidget(self)
        crawler_layout.addWidget(self.marquee)
        main_layout.addWidget(self.crawler_capsule, stretch=1)

        # 4. Situational Alert & Local Clock
        self.alert_badge = QLabel("")
        self.alert_badge.setObjectName("alert_badge")
        self.alert_badge.hide()
        main_layout.addWidget(self.alert_badge)

        self.clock_label = QLabel("")
        self.clock_label.setObjectName("clock_label")
        main_layout.addWidget(self.clock_label)

        self.apply_theme()
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

    def apply_theme(self):
        cfg = SPORTS_CONFIG[self.current_sport]
        color = cfg["primary_color"]

        self.setStyleSheet(f"""
            MultiSportTicker {{
                background-color: #0b0c0e;
                border-top: 2px solid {color};
            }}
            QLabel {{
                color: #FFFFFF;
                font-family: 'Segoe UI', Arial, sans-serif;
                border: none;
            }}
            #featured_capsule {{
                background-color: #12141a;
                border: 1px solid #232733;
                border-radius: 6px;
            }}
            #crawler_capsule {{
                background-color: #101217;
                border: 1px solid #1f232e;
                border-radius: 6px;
            }}
            #game_clock {{
                color: #00E676;
                font-weight: 800;
                font-size: 13px;
                padding: 0 10px;
                border: none;
            }}
            #alert_badge {{
                background-color: #FBBF24;
                color: #000000;
                font-weight: 900;
                font-size: 11px;
                padding: 4px 10px;
                border-radius: 4px;
                letter-spacing: 0.5px;
                border: none;
            }}
            #clock_label {{
                background-color: #12141a;
                border: 1px solid #232733;
                border-radius: 4px;
                color: #CBD5E1;
                font-size: 12px;
                font-weight: 700;
                padding: 4px 10px;
            }}
            QMenu {{
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #444444;
                font-size: 13px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 20px;
            }}
            QMenu::item:selected {{
                background-color: {color};
            }}
        """)
        self.brand_badge.set_sport(self.current_sport)

    def cycle_sport(self, target_sport=None):
        if target_sport and target_sport in self.sports:
            self.current_sport = target_sport
            self.current_sport_idx = self.sports.index(target_sport)
        else:
            self.current_sport_idx = (self.current_sport_idx + 1) % len(self.sports)
            self.current_sport = self.sports[self.current_sport_idx]

        self.apply_theme()
        self.games = []
        self.current_game_index = 0
        
        self.away_abbr.setText("---")
        self.away_score.setText("0")
        self.home_abbr.setText("---")
        self.home_score.setText("0")
        self.game_clock.setText(f"FETCHING {self.current_sport}...")
        self.away_logo.hide()
        self.home_logo.hide()
        self.alert_badge.hide()
        self.marquee.set_segments([])

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
        self.worker = ScoreWorker(self.current_sport)
        self.worker.data_ready.connect(self.on_data_loaded)
        self.worker.start()

    def on_data_loaded(self, parsed_games, raw_logos, sport_key):
        if sport_key != self.current_sport:
            return

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
        
        if not self.games:
            self.game_clock.setText("NO GAMES TODAY")
        else:
            self.cycle_featured_game()

    def get_pixmap(self, url, size=24):
        if url in self.logo_cache and size in self.logo_cache[url]:
            return self.logo_cache[url][size]
        return None

    def update_crawler_segments(self):
        segments = []
        cfg = SPORTS_CONFIG[self.current_sport]

        if not self.games:
            segments.append({"type": "text", "content": f"NO SCHEDULED {self.current_sport} GAMES TODAY", "color": "#94A3B8", "spacing": 40})
            self.marquee.set_segments(segments)
            return

        for g in self.games:
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

            segments.append({"type": "text", "content": "★", "color": cfg["primary_color"], "spacing": 22})

        self.marquee.set_segments(segments)

    def cycle_featured_game(self):
        if not self.games:
            return
        
        game = self.games[self.current_game_index]

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

        sport_menu = menu.addMenu("Switch Sport...")
        for sp in self.sports:
            label = f"{sp}"
            if sp == self.current_sport:
                label += " ✓"
            action = QAction(label, self)
            action.triggered.connect(lambda checked, s=sp: self.cycle_sport(target_sport=s))
            sport_menu.addAction(action)

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
    ticker = MultiSportTicker(initial_screen_index=0)
    ticker.show()
    sys.exit(app.exec())