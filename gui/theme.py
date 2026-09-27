"""
Theme module: purple palette, animated gradient background, global QSS.
"""
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QLinearGradient, QColor, QPainter
from PyQt5.QtWidgets import QWidget


# ---- Purple palette ---------------------------------------------------
PURPLE_DARK = "#1a0b2e"
PURPLE_MID = "#3c1361"
PURPLE_ACCENT = "#8e2de2"
PURPLE_ACCENT2 = "#b06ab3"
PURPLE_LIGHT = "#d6a4ff"
PINK_ACCENT = "#e85fbf"
TEXT_LIGHT = "#f3e9ff"
SUCCESS = "#7ee787"
ERROR = "#ff6b81"


class AnimatedBackground(QWidget):
    """A widget that paints a slowly-shifting purple gradient behind everything else."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._angle = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(45)  # ~22 fps, gentle motion

    def _tick(self):
        self._angle = (self._angle + 0.6) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        # Shift gradient start/stop points based on angle for a slow swirling feel
        import math
        rad = math.radians(self._angle)
        x1 = w / 2 + math.cos(rad) * w
        y1 = h / 2 + math.sin(rad) * h
        x2 = w / 2 - math.cos(rad) * w
        y2 = h / 2 - math.sin(rad) * h

        grad = QLinearGradient(x1, y1, x2, y2)
        grad.setColorAt(0.0, QColor(PURPLE_DARK))
        grad.setColorAt(0.45, QColor(PURPLE_MID))
        grad.setColorAt(0.75, QColor(PURPLE_ACCENT))
        grad.setColorAt(1.0, QColor(PINK_ACCENT))

        painter.fillRect(self.rect(), grad)
        super().paintEvent(event)


GLOBAL_QSS = f"""
QWidget {{
    color: {TEXT_LIGHT};
    font-family: 'Segoe UI', 'Ubuntu', sans-serif;
    font-size: 13px;
}}

QLabel#TitleLabel {{
    font-size: 26px;
    font-weight: 800;
    letter-spacing: 1px;
}}

QLabel#SubtitleLabel {{
    font-size: 12px;
    color: {PURPLE_LIGHT};
}}

QLineEdit, QPlainTextEdit {{
    background-color: rgba(255, 255, 255, 25);
    border: 1px solid {PURPLE_ACCENT2};
    border-radius: 8px;
    padding: 8px;
    color: {TEXT_LIGHT};
    selection-background-color: {PINK_ACCENT};
}}

QLineEdit:focus {{
    border: 1px solid {PINK_ACCENT};
}}

QListWidget, QTableWidget {{
    background-color: rgba(20, 6, 40, 130);
    border: 1px solid {PURPLE_ACCENT2};
    border-radius: 10px;
    gridline-color: rgba(255,255,255,20);
}}

QHeaderView::section {{
    background-color: {PURPLE_MID};
    color: {TEXT_LIGHT};
    padding: 6px;
    border: none;
    font-weight: 600;
}}

QTableWidget::item {{
    padding: 4px;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 10px;
}}
QScrollBar::handle:vertical {{
    background: {PURPLE_ACCENT2};
    border-radius: 5px;
    min-height: 24px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QPlainTextEdit#LogConsole {{
    background-color: rgba(10, 3, 20, 160);
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 11px;
    color: {PURPLE_LIGHT};
}}

QProgressBar {{
    border: 1px solid {PURPLE_ACCENT2};
    border-radius: 8px;
    background-color: rgba(255,255,255,20);
    text-align: center;
    color: {TEXT_LIGHT};
    height: 18px;
}}

QProgressBar::chunk {{
    border-radius: 7px;
    background-color: {PURPLE_ACCENT};
}}

QComboBox {{
    background-color: rgba(255,255,255,25);
    border: 1px solid {PURPLE_ACCENT2};
    border-radius: 8px;
    padding: 6px;
}}

QToolTip {{
    background-color: {PURPLE_DARK};
    color: {TEXT_LIGHT};
    border: 1px solid {PURPLE_ACCENT2};
}}
"""
