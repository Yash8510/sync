"""
Custom UI widgets: floating orb
"""

import math
import logging

from PyQt6.QtCore import Qt, QPoint, QPointF, QTimer
from PyQt6.QtGui import QPainter, QPen, QColor, QPainterPath, QRadialGradient
from PyQt6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class FloatingOrb(QWidget):
    """A Floating Orb with smooth wave animations reacting to audio level"""

    def __init__(self):
        super().__init__()

        self.setFixedSize(100, 100)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)  # set translucent background

        self.drag_position = QPoint()  # storing drag position

        self.phase = 0.0
        self.target_audio_level = 0.0
        self.current_audio_level = 0.0

        # Animation timer to drive the wave phase update (60 FPS)
        self.anim_timer = QTimer(self)
        self.anim_timer.setInterval(16)  # ~16ms for 60 FPS
        self.anim_timer.timeout.connect(self._animate)
        self.anim_timer.start()

    def set_audio_level(self, level: float) -> None:
        """Set the target audio level (0.0 to 1.0)"""
        self.target_audio_level = max(0.0, min(level, 1.0))

    def _animate(self) -> None:
        # Increment wave phase; speed increases slightly when louder
        speed = 0.05 + self.current_audio_level * 0.08
        self.phase += speed
        if self.phase > 2 * math.pi * 100:
            self.phase -= 2 * math.pi * 100

        # Smoothly ease current audio level towards target level for fluid transitions
        self.current_audio_level = self.current_audio_level * 0.8 + self.target_audio_level * 0.2

        # Request repaint
        self.update()

    def _draw_wave_layer(
        self,
        painter: QPainter,
        radius: float,
        base_amp: float,
        phase_offset: float,
        fill_color: QColor,
        stroke_color: QColor
    ) -> None:
        path = QPainterPath()
        steps = 80
        for i in range(steps + 1):
            theta = (i / steps) * 2 * math.pi

            # Scale amplitude based on the current reactive audio level
            amp_mod = base_amp * (1.0 + 5.0 * self.current_audio_level)

            # Sum of harmonics to create a highly organic fluid motion
            offset1 = math.sin(3 * theta - self.phase + phase_offset)
            offset2 = math.cos(5 * theta + self.phase * 1.4 - phase_offset)

            r = radius + amp_mod * (offset1 * 0.65 + offset2 * 0.35)

            x = 50.0 + r * math.cos(theta)
            y = 50.0 + r * math.sin(theta)

            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)

        path.closeSubpath()

        # Fill inside path
        painter.fillPath(path, fill_color)

        # Draw path outline
        pen = QPen(stroke_color, 1.5)
        painter.setPen(pen)
        painter.drawPath(path)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Background glow
        bg_glow = QRadialGradient(50.0, 50.0, 48.0)
        bg_glow.setColorAt(0.0, QColor(100, 50, 255, int(40 + 80 * self.current_audio_level)))
        bg_glow.setColorAt(0.6, QColor(0, 200, 255, int(15 + 40 * self.current_audio_level)))
        bg_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg_glow)
        painter.drawEllipse(QPointF(50.0, 50.0), 48.0, 48.0)

        # 2. Outer wave (Deep purple)
        self._draw_wave_layer(
            painter,
            radius=30.0,
            base_amp=2.0,
            phase_offset=0.0,
            fill_color=QColor(100, 50, 255, 30),
            stroke_color=QColor(120, 80, 255, 140)
        )

        # 3. Middle wave (Vibrant magenta)
        self._draw_wave_layer(
            painter,
            radius=26.0,
            base_amp=2.5,
            phase_offset=math.pi / 3,
            fill_color=QColor(255, 0, 150, 35),
            stroke_color=QColor(255, 50, 180, 170)
        )

        # 4. Inner wave (Electric cyan)
        self._draw_wave_layer(
            painter,
            radius=22.0,
            base_amp=1.8,
            phase_offset=2 * math.pi / 3,
            fill_color=QColor(0, 230, 255, 40),
            stroke_color=QColor(0, 255, 255, 200)
        )

        # 5. Glowing center core
        core_radius = 16.0 + 5.0 * self.current_audio_level + math.sin(self.phase * 3.0) * 0.8
        core_grad = QRadialGradient(50.0, 50.0, core_radius)
        core_grad.setFocalPoint(47.0, 47.0)  # Offset center slightly for 3D sphere illusion
        core_grad.setColorAt(0.0, QColor(255, 255, 255, 240))
        core_grad.setColorAt(0.4, QColor(100, 220, 255, 220))
        core_grad.setColorAt(0.8, QColor(130, 0, 255, 130))
        core_grad.setColorAt(1.0, QColor(130, 0, 255, 0))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(core_grad)
        painter.drawEllipse(QPointF(50.0, 50.0), core_radius, core_radius)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

