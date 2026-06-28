import sys
import math
import random
from PyQt6.QtCore import Qt, QTimer, QPoint, QPointF
from PyQt6.QtGui import QPainter, QColor, QPainterPath, QBrush
from PyQt6.QtWidgets import QApplication, QWidget

class ParametricOrb(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(300, 300)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.drag_position = QPoint()

        # Animation & Simulation Variables
        self.phase = 0.0
        self.audio_level = 0.5  # Simulates mock audio amplitude (0.0 to 1.0)
        
        # Timer to drive the animation loop (approx 60 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_deformation)
        self.timer.start(16)

    def update_deformation(self):
        # 1. Advance time phase for smooth organic evolution
        self.phase += 0.05
        
        # 2. Simulate fluctuating audio data (Replace this with real audio stream data later)
        # We simulate a base rhythm with occasional random spikes
        self.audio_level = 0.4 + 0.3 * math.sin(self.phase * 0.5) + random.uniform(0, 0.2)
        
        # 3. Force a redraw (Triggers paintEvent)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x = self.width() / 2
        center_y = self.height() / 2
        base_radius = 80
        
        # Create a blank geometric vector path
        path = QPainterPath()
        
        num_points = 100  # More points = smoother deformation
        points = []
        
        for i in range(num_points):
            # Calculate angle theta from 0 to 2*PI
            theta = (i / num_points) * 2 * math.pi
            
            # --- THE PARAMETRIC FORMULA ---
            # We modulate the radius dynamically at this specific angle using sine waves.
            # 'self.phase' moves the waves over time. 
            # 'self.audio_level' scales how violent/noticeable the deformation is.
            distortion = (
                math.sin(theta * 4 + self.phase) * 15 +   # Low frequency wobble (Bass)
                math.cos(theta * 9 - self.phase * 2) * 8  # Higher frequency ripples (Mids/Treble)
            ) * self.audio_level
            
            r = base_radius + distortion
            
            # Convert polar coordinates (r, theta) back to Cartesian pixels (x, y)
            x = center_x + r * math.cos(theta)
            y = center_y + r * math.sin(theta)
            points.append(QPointF(x, y))
            
        # Build the vector shape path by connecting the dots
        path.moveTo(points[0])
        for pt in points[1:]:
            path.lineTo(pt)
        path.closeSubpath() # Snap back to the beginning to close the loop smoothly
        
        # Paint the dynamic shape
        orb_color = QColor(88, 101, 242, 220) # Discord Blurple
        painter.fillPath(path, QBrush(orb_color))

    # --- Mouse Dragging Mechanics ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    orb = ParametricOrb()
    orb.show()
    sys.exit(app.exec())