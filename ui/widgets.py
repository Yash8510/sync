"""
Custom UI widgets: floating orb redesigned to match holographic 3D wireframe style (optimized with blue gradient theme)
"""

import math

from PyQt6.QtCore import Qt, QPoint, QPointF
from PyQt6.QtGui import QPainter, QPen, QColor, QRadialGradient, QConicalGradient, QBrush
from PyQt6.QtWidgets import QWidget


class FloatingOrb(QWidget):
    """A Floating Orb redesigned as a 3 dotted-wave visualizer with animated blue gradients"""

    def __init__(self):
        super().__init__()

        # Size of the widget (200x200 pixels)
        self.size = [200, 200]
        self.setFixedSize(self.size[0], self.size[1])

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        self.drag_position = QPoint()

        # Animation states
        self.phase = 0.0
        self.target_audio_level = 0.0
        self.current_audio_level = 0.0

        self.target_bass_level = 0.0
        self.current_bass_level = 0.0
        self.target_mid_level = 0.0
        self.current_mid_level = 0.0
        self.target_treble_level = 0.0
        self.current_treble_level = 0.0

        self.fft_bands = [0.0] * 16
        self.smooth_fft_bands = [0.0] * 16

        # Optimization: Precompute circle coordinates (60 steps is perfect for distinct points)
        self.steps = 60
        self.trig_cache = []
        for i in range(self.steps):
            theta = (i / self.steps) * 2 * math.pi
            self.trig_cache.append((theta, math.cos(theta), math.sin(theta)))

    def set_audio_level(self, level: float) -> None:
        """Set the target audio level (0.0 to 1.0)"""
        self.target_audio_level = max(0.0, min(level, 1.0))
        self.target_bass_level = self.target_audio_level
        self.target_mid_level = self.target_audio_level
        self.target_treble_level = self.target_audio_level

    def set_audio_data(self, level: float, fft_bands, bass_level: float, mid_level: float, treble_level: float) -> None:
        """Set detailed audio levels and FFT frequency bands"""
        self.target_audio_level = max(0.0, min(level, 1.0))
        self.target_bass_level = max(0.0, min(bass_level, 1.0))
        self.target_mid_level = max(0.0, min(mid_level, 1.0))
        self.target_treble_level = max(0.0, min(treble_level, 1.0))

        if len(fft_bands) == 16:
            self.fft_bands = [max(0.0, min(b, 1.0)) for b in fft_bands]

        # Drive animation step and repaint immediately (fully synchronized)
        self._animate()

    def _animate(self) -> None:
        # Update system phase
        speed = 0.03 + self.current_audio_level * 0.06
        self.phase += speed
        if self.phase > 2 * math.pi * 100:
            self.phase -= 2 * math.pi * 100

        # Snappy easing (0.65 old / 0.35 new) for immediate, lag-free responsiveness
        self.current_audio_level = self.current_audio_level * 0.60 + self.target_audio_level * 0.40
        self.current_bass_level = self.current_bass_level * 0.60 + self.target_bass_level * 0.40
        self.current_mid_level = self.current_mid_level * 0.60 + self.target_mid_level * 0.40
        self.current_treble_level = self.current_treble_level * 0.60 + self.target_treble_level * 0.40

        # Smooth FFT bands
        for i in range(16):
            self.smooth_fft_bands[i] = self.smooth_fft_bands[i] * 0.6 + self.fft_bands[i] * 0.4

        # Request repaint
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx = self.size[0] / 2
        cy = self.size[1] / 2

        # 1. Background glow (Deep Royal/Neon Blue vignette - boosted saturation and brightness)
        bg_grad = QRadialGradient(cx, cy, self.size[0] / 2)  # center gradient color
        bg_grad.setColorAt(0.0, QColor(0, 102, 255, int(60 + 80 * self.current_audio_level)))  # Saturated Neon Blue center
        bg_grad.setColorAt(0.6, QColor(0, 25, 120, int(20 + 35 * self.current_audio_level)))   # Vivid deep blue
        bg_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(bg_grad)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), 96.0, 96.0)

        # 2. Outer Wavy Particle Rings (Boosted base opacity for maximum visibility)
        wave_configs = [
            # radius, freq, amp, phase_offset, level (Bass/Mid/Treble), alpha
            (76.0, 5, 0.5 + 18.0 * self.current_bass_level, self.phase, self.current_bass_level, 255), # Fully solid base
            (80.0, 7, 0.5 + 14.0 * self.current_mid_level, -self.phase * 1.3, self.current_mid_level, 210),
            (84.0, 4, 0.5 + 10.0 * self.current_treble_level, self.phase * 0.8, self.current_treble_level, 170)
        ]

        # Slowly rotate the circular gradient around the center to make colors cycle
        gradient_angle = math.degrees(self.phase * 0.4)

        for r_base, freq, amp, p_off, reactivity, alpha in wave_configs:
            points = []
            for theta, cos_t, sin_t in self.trig_cache:
                # Modulate radius based on cached angles and current frequency phase
                r = r_base + amp * math.sin(freq * theta + p_off)
                x = cx + r * cos_t
                y = cy + r * sin_t
                points.append(QPointF(x, y))

            # Create a conical gradient centered at the widget center
            gradient = QConicalGradient(cx, cy, gradient_angle)
            
            # Keep minimum opacity very high (80%) so colors look thick and visible even in quiet states
            alpha_val = int(alpha * (0.8 + 0.2 * reactivity))
            gradient.setColorAt(0.0, QColor(0, 255, 255, alpha_val))   # Solid Cyan
            gradient.setColorAt(0.25, QColor(0, 150, 255, alpha_val))  # Vivid Blue
            gradient.setColorAt(0.5, QColor(100, 30, 255, alpha_val))  # Vivid Purple-Indigo
            gradient.setColorAt(0.75, QColor(0, 150, 255, alpha_val))  # Vivid Blue
            gradient.setColorAt(1.0, QColor(0, 255, 255, alpha_val))   # Solid Cyan

            # Thicker pen (3.5px instead of 1.5px) for bolder, more visible particle rings
            pen = QPen(QBrush(gradient), 3.5)
            painter.setPen(pen)
            painter.drawPoints(points)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
