"""
Custom animated PyQt5 widgets used throughout the app:
 - GlowButton: a QPushButton with an animated drop-shadow glow on hover
 - AnimatedProgressBar: a QProgressBar whose value animates smoothly and whose
   chunk color slowly pulses through shades of purple/pink while active
"""
from PyQt5.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QTimer, QVariantAnimation
)
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QPushButton, QProgressBar, QGraphicsDropShadowEffect

from .theme import PURPLE_ACCENT, PURPLE_ACCENT2, PINK_ACCENT, PURPLE_LIGHT, TEXT_LIGHT


class GlowButton(QPushButton):
    """A button that glows with a soft purple/pink shadow when hovered, and
    briefly flashes bright when clicked."""

    def __init__(self, text="", base_color=PURPLE_ACCENT, parent=None):
        super().__init__(text, parent)
        self.base_color = QColor(base_color)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(36)
        self.setStyleSheet(self._style(self.base_color))

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(0)
        self._shadow.setColor(QColor(PINK_ACCENT))
        self._shadow.setOffset(0, 0)
        self.setGraphicsEffect(self._shadow)

        self._anim = QPropertyAnimation(self._shadow, b"blurRadius", self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    def _style(self, color: QColor):
        return f"""
            QPushButton {{
                background-color: {color.name()};
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
                color: {TEXT_LIGHT};
            }}
            QPushButton:hover {{
                background-color: {PINK_ACCENT};
            }}
            QPushButton:pressed {{
                background-color: {PURPLE_LIGHT};
                color: #2a0a45;
            }}
            QPushButton:disabled {{
                background-color: #55406b;
                color: #b9a7cc;
            }}
        """

    def enterEvent(self, event):
        self._anim.stop()
        self._anim.setStartValue(self._shadow.blurRadius())
        self._anim.setEndValue(25)
        self._anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._anim.stop()
        self._anim.setStartValue(self._shadow.blurRadius())
        self._anim.setEndValue(0)
        self._anim.start()
        super().leaveEvent(event)


class AnimatedProgressBar(QProgressBar):
    """A progress bar that:
      - animates value transitions smoothly instead of jumping
      - pulses its fill color through a purple->pink->purple cycle while active
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(True)
        self.setRange(0, 100)
        self._value_anim = QPropertyAnimation(self, b"value", self)
        self._value_anim.setDuration(350)
        self._value_anim.setEasingCurve(QEasingCurve.OutCubic)

        self._color_anim = QVariantAnimation(self)
        self._color_anim.setStartValue(QColor(PURPLE_ACCENT))
        self._color_anim.setKeyValueAt(0.5, QColor(PINK_ACCENT))
        self._color_anim.setEndValue(QColor(PURPLE_ACCENT))
        self._color_anim.setDuration(2200)
        self._color_anim.setLoopCount(-1)
        self._color_anim.valueChanged.connect(self._apply_color)
        self._color_anim.start()
        self._active = True

        self.set_chunk_color(QColor(PURPLE_ACCENT))

    def animate_to(self, value: int):
        self._value_anim.stop()
        self._value_anim.setStartValue(self.value())
        self._value_anim.setEndValue(value)
        self._value_anim.start()

    def set_active(self, active: bool):
        self._active = active
        if active:
            self._color_anim.start()
        else:
            self._color_anim.stop()

    def _apply_color(self, color: QColor):
        if self._active:
            self.set_chunk_color(color)

    def set_chunk_color(self, color: QColor):
        self.setStyleSheet(f"""
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
                background-color: {color.name()};
            }}
        """)

    def mark_success(self):
        self.set_active(False)
        self.set_chunk_color(QColor("#7ee787"))

    def mark_error(self):
        self.set_active(False)
        self.set_chunk_color(QColor("#ff6b81"))
